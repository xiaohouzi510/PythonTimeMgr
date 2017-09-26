#!/usr/bin/python
# coding=utf-8

import time

TIMER_LIST_NR   = 256 			#数组个数 
TIMER_LIST_MASK = 255 			#掩码 
TICK_MASK		= 0xffffffff    #tick 掩码	

#定时器双向链表结点
class TimeNode:
	def __init__(self,fFunCb,iExpireTick,iTime,bIsLoop,iSession,stData):
		self.m_stData   	= stData
		self.m_fFunCb   	= fFunCb
		self.m_iExpireTick  = iExpireTick
		self.m_iSession 	= iSession
		self.m_iTime    	= iTime
		self.m_stNext 		= None
		self.m_stFront  	= None
		self.m_bIsLoop      = bIsLoop

	#重置
	def Reset(self):
		self.m_stNext 		= None
		self.m_stFront  	= None
		self.m_iExpireTick  = 0

#定时器双向链表
class TimeLink:
	def __init__(self):
		self.m_stHead = None
		self.m_stTail = None

#----------定时器,单位为10毫秒-----------
class TimeMgr:
	def __init__(self):
		self.m_iSession  = 4294967293
		self.m_szData    = []
		self.m_iCurTick  = 4294967293 
		self.m_hData	 = {}
		self.m_iLastTime = self.GetCurTime()
		for i in range(1,TIMER_LIST_NR+1):
			self.m_szData.append(TimeLink())

	#获得当前时间，单位为10毫秒
	def GetCurTime(self):
		return int(round(time.time() * 100))

	#根据超时时间获得索引
	def HashCode(self,iExpireTick):
		return TIMER_LIST_MASK & iExpireTick

	#添加定时器
	#param fFunCb 回调函数
	#param iTime 循环时间，单位为毫秒
	#param bIsLoop 是否循环
	#param stData 用户数据，回调时作为参数
	def AddTimer(self,fFunCb,iTime,bIsLoop,stData):
		iExpireTick = (self.GetTick(iTime) + self.m_iCurTick)&TICK_MASK
		iCurSession = self.MakeSession()
		stTimeNode  = TimeNode(fFunCb,iExpireTick,iTime,bIsLoop,iCurSession,stData)

		iIndex = self.AddTail(stTimeNode)
		self.m_hData[stTimeNode.m_iSession] = stTimeNode
		return iCurSession

	#尾插法添加一个节点	
	def AddTail(self,stTimeNode):
		iIndex 		= self.HashCode(stTimeNode.m_iExpireTick)
		stTimeLink  = self.m_szData[iIndex]
		if stTimeLink.m_stHead == None:
			stTimeLink.m_stHead = stTimeNode
			stTimeLink.m_stTail = stTimeNode
		else:
			stTimeNode.m_stFront = stTimeLink.m_stTail
			stTimeLink.m_stTail.m_stNext = stTimeNode
			stTimeLink.m_stTail  = stTimeNode
		return iIndex	

	#头插法添加一个节点
	def AddHead(self,stTimeNode):
		iIndex 		= self.HashCode(stTimeNode.m_iExpireTick)
		stTimeLink  = self.m_szData[iIndex]
		if stTimeLink.m_stHead == None:
			stTimeLink.m_stHead = stTimeNode
			stTimeLink.m_stTail = stTimeNode
		else:
			stTimeLink.m_stHead.m_stFront = stTimeNode
			stTimeNode.m_stNext = stTimeLink.m_stHead
			stTimeLink.m_stHead = stTimeNode
		return iIndex

	#时间转成 tick，一个 tick 为10毫秒
	def GetTick(self,iTime):
		return int(iTime/10)

	#生成一个 session ,对应一个 TimeNode
	def MakeSession(self):
		iResultSession = 0
		while True:
			#0不使用
			if self.m_iSession == 0:
				self.m_iSession = 1
			iResultSession  = self.m_iSession
			#最大为 4294967295
			self.m_iSession = (self.m_iSession + 1)&TICK_MASK
			if self.m_hData.has_key(iResultSession) == False:
				break
		return iResultSession

	#定时更新
	def UpdateTime(self):
		iCurTime = self.GetCurTime()
		iTickCount = iCurTime - self.m_iLastTime
		if iTickCount < 2:
			return
		iLastTick = self.m_iCurTick
		self.m_iCurTick = self.m_iCurTick + iTickCount
		#最大为 4294967295
		self.m_iCurTick = self.m_iCurTick&TICK_MASK

		self.m_iLastTime = iCurTime 
		for i in range(0,iTickCount+1):
			iCurTick = (iLastTick + i)&TICK_MASK
			iIndex = self.HashCode(iCurTick)
			stTimeLink = self.m_szData[iIndex]
			self.TimeExecute(stTimeLink,iCurTick)

	#执行回调
	def TimeExecute(self,stTimeLink,iCurTick):
		stCurNode  = stTimeLink.m_stHead
		stTempNode = None
		while stCurNode != None:
			if iCurTick == stCurNode.m_iExpireTick:				
				stTempNode = stCurNode
				stCurNode = stCurNode.m_stNext
				self.RemoveNode(stTimeLink,stTempNode)
				
				stTempNode.Reset()
				stTempNode.m_iExpireTick  = self.GetTick(stTempNode.m_iTime) + self.m_iCurTick
				if stTempNode.m_bIsLoop:
					self.AddHead(stTempNode)

				#回调放后面，防止在回调期间注册定时器，导致链表出错
				stTempNode.m_fFunCb(stTempNode.m_stData)
			else:
				stCurNode = stCurNode.m_stNext

		if stTimeLink.m_stHead == None:
			stTimeLink.m_stTail = None

	#删除定时器	
	def RemoveTimer(self,iSession):
		if self.m_hData.has_key(iSession) == False:
			return False

		stTimeNode = self.m_hData[iSession]
		iIndex 	   = self.HashCode(stTimeNode.m_iExpireTick)
		stTimeLink = self.m_szData[iIndex]
		self.RemoveNode(stTimeLink,stTimeNode)
		del self.m_hData[iSession]

		return True

	#删除结点
	def RemoveNode(self,stTimeLink,stTimeNode):
		if stTimeNode.m_stFront != None:
			stTimeNode.m_stFront.m_stNext = stTimeNode.m_stNext
		else:
			stTimeLink.m_stHead = stTimeNode.m_stNext

		if stTimeNode.m_stNext != None:
			stTimeNode.m_stNext.m_stFront = stTimeNode.m_stFront
		else:
			stTimeLink.m_stTail = stTimeNode.m_stFront

	#打印所有定时器
	def Display(self):
		iTotal = 0
		for i in range(0,TIMER_LIST_NR):	
			stTimeLink = self.m_szData[i]
			stCurNode = stTimeLink.m_stHead
			iOneNode = 0
			while stCurNode != None:
				iTotal = iTotal + 1
				iOneNode = iOneNode + 1
				print("list index %d expire %d session %d time %d index %d"%(i,stCurNode.m_iExpireTick,stCurNode.m_iSession,stCurNode.m_iTime,iOneNode))
				stCurNode = stCurNode.m_stNext
		print("---------------------%d"%(iTotal))