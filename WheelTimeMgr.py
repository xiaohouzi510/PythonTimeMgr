#!/usr/bin/python
# coding=utf-8

import time
import logging

logger = logging.getLogger(__name__)

#----------参数----------
TIME_NEAR_SHIFT  = 8
TIME_NEAR 		 = (1 << TIME_NEAR_SHIFT)
TIME_LEVEL_SHIFT = 6
TIME_LEVEL 		 = (1 << TIME_LEVEL_SHIFT)
TIME_NEAR_MASK   = (TIME_NEAR-1)
TIME_LEVEL_MASK  = (TIME_LEVEL-1)
TICK_MASK		 = 0xffffffff    #tick 掩码

#定时器双向链表结点
class TimeNode:
	def __init__(self,iTime,bLoop):
		self.m_iExpire  	= 0 
		self.m_iSession 	= 0 
		self.m_iTime    	= iTime
		self.m_stNext 		= None
		self.m_stFront  	= None
		self.m_iId 			= 0 
		self.m_bLoop        = bLoop
		self.m_stFather 	= None
		self.m_fCb 			= None
		self.m_stData 		= None

	#重置
	def Reset(self):
		self.m_stNext 		= None
		self.m_stFront  	= None

#定时器双向链表
class TimeLink:
	def __init__(self):
		self.m_stHead = None
		self.m_stTail = None

#---------分级时间轮定时器-------------
class WheelTimerMgr:
	def __init__(self):
		#前 255 个链表定时器 
		self.m_szNear     = []
		#每级 64 链表定时器，总共 6 级
		self.m_szLevel    = []
		#当前嘀嗒
		self.m_iCurTick   = 0
		#最后一次系统时间
		self.m_iLastTime  = self.GetCurTime()
		#锁
		self.m_stLock     = None 
		#初始化
		self.Init()
		#所有结点
		self.m_hData      = {}

		#获得当前时间，单位为10毫秒
	def GetCurTime(self):
		return int(round(time.time() * 100))

	#上锁
	def Lock(self):
		self.m_stLock != None and self.m_stLock.Lock()

	#解锁
	def UnLock(self):
		self.m_stLock != None and self.m_stLock.UnLock()

	#初始化函数
	def Init(self):
		for i in range(0,TIME_NEAR):
			self.m_szNear.append(TimeLink())

		for i in range(0,TIME_LEVEL_SHIFT):
			self.m_szLevel.append([])
			for j in range(0,TIME_LEVEL):
				self.m_szLevel[i].append(TimeLink())

	#尾插法添加一个节点
	def AddTail(self,stTimeLink,stTimeNode):
		stTimeNode.m_stFather = stTimeLink
		if stTimeLink.m_stHead == None:
			stTimeLink.m_stHead = stTimeNode
			stTimeLink.m_stTail = stTimeNode
		else:
			stTimeNode.m_stFront = stTimeLink.m_stTail
			stTimeLink.m_stTail.m_stNext = stTimeNode
			stTimeLink.m_stTail  = stTimeNode

	#头插法添加一个节点
	def AddHead(self,stTimeLink,stTimeNode):
		stTimeNode.m_stFather = stTimeLink
		if stTimeLink.m_stHead == None:
			stTimeLink.m_stHead = stTimeNode
			stTimeLink.m_stTail = stTimeNode
		else:
			stTimeLink.m_stHead.m_stFront = stTimeNode
			stTimeNode.m_stNext = stTimeLink.m_stHead
			stTimeLink.m_stHead = stTimeNode

	#添加一个节点
	def AddNode(self,stTimeNode):
		iExpire = stTimeNode.m_iExpire
		if iExpire|TIME_NEAR_MASK == self.m_iCurTick|TIME_NEAR_MASK:
			self.AddTail(self.m_szNear[iExpire&TIME_NEAR_MASK],stTimeNode)
		else:
			iMask  = TIME_NEAR << TIME_LEVEL_SHIFT
			iLevel = 0
			for i in range(0,3):
				if iExpire|(iMask - 1) == self.m_iCurTick|(iMask - 1):
					break
				iMask  = iMask << TIME_LEVEL_SHIFT	
				iLevel = iLevel + 1
			self.AddTail(self.m_szLevel[iLevel][iExpire >> (TIME_NEAR_SHIFT + iLevel*TIME_LEVEL_SHIFT)],stTimeNode)

	#移动一个链表
	def MoveList(self,iLevel,iIndex):
		stTimeNode = self.LinkClear(self.m_szLevel[iLevel][iIndex])
		stNextNode = None
		while stTimeNode != None: 
			stNextNode = stTimeNode.m_stNext 
			stTimeNode.Reset()
			self.AddNode(stTimeNode)
			stTimeNode = stNextNode

	#清空一个链表并返回结点
	def LinkClear(self,stTimeLink):
		stTimeNode = stTimeLink.m_stHead
		stTimeLink.m_stHead = None
		stTimeLink.m_stTail = None
		return stTimeNode

	#轮移动
	def TimerShift(self):
		self.m_iCurTick = (self.m_iCurTick + 1)&TICK_MASK
		if self.m_iCurTick == 0:
			self.MoveList(3,0)
		else:
			iCurTick = self.m_iCurTick >> TIME_NEAR_SHIFT
			iMask    = TIME_NEAR
			iLevel   = 0
			while self.m_iCurTick & (iMask - 1) == 0:
				iIndex = iCurTick & TIME_LEVEL_MASK
				if iIndex != 0:
					self.MoveList(iLevel,iIndex)
					break
				iLevel   = iLevel + 1
				iMask    = iMask << TIME_LEVEL_SHIFT
				iCurTick = iCurTick >> TIME_LEVEL_SHIFT

	#更新定时器
	def UpdateTime(self):
		iCurTime = self.GetCurTime()
		iCount   = iCurTime - self.m_iLastTime 
		if iCount <= 0:
			return
		self.m_iLastTime = iCurTime  
		for i in range(0,iCount):
			self.Lock()
			self.TimerShift()	
			self.TimeExecute()
			self.UnLock()

	#执行定时器
	def TimeExecute(self):
		iIndex = self.m_iCurTick & TIME_NEAR_MASK
		stTimeNode = self.LinkClear(self.m_szNear[iIndex])
		if stTimeNode == None:
			return
		self.DispatchList(stTimeNode)

	#转发定时器消息
	def DispatchList(self,stTimeNode):
		stCurNode = stTimeNode
		while stTimeNode != None:
			stCurNode = stTimeNode.m_stNext
			self.UnLock()
			stTimeNode.m_fCb(stTimeNode.m_stData)
			self.Lock()
			if stTimeNode.m_bLoop:
				stTimeNode.Reset()
				stTimeNode.m_iExpire = self.GetExpire(stTimeNode.m_iTime)
				self.AddNode(stTimeNode)
			else:
				self.RemoveSession(stTimeNode.m_iId,stTimeNode.m_iSession)
			stTimeNode = stCurNode

	#添加定时器
	def AddTimer(self,stTimeNode):	
		iId 	 = stTimeNode.m_iId
		iSession = stTimeNode.m_iSession
		iTime    = stTimeNode.m_iTime
		self.Lock()
		if not self.m_hData.has_key(iId):
			self.m_hData[iId] = {}
		stOne = self.m_hData[iId]
		if stOne.has_key(iSession):
			self.UnLock()
			print("double timer session=%d id=%d time=%d"%(iSession,iId,iTime))
			return
		stTimeNode.m_iExpire = self.GetExpire(iTime)
		stOne[iSession] = stTimeNode
		self.AddNode(stTimeNode)	
		self.UnLock()

	#获得超时时间，一个 tick 为10毫秒
	def GetExpire(self,iTime):
		return self.m_iCurTick + int(iTime/10)

	#删除 session
	def RemoveSession(self,iId,iSession):
		stOne = self.m_hData[iId]	
		stTimeNode = stOne[iSession]
		del stOne[iSession]
		return stTimeNode

	#删除定时器
	def RemoveTimer(self,iId,iSession):
		self.Lock()
		if self.m_hData.has_key(iId):
			print("remove timer not found id=%d session=%d"%(iId,iSession))
			self.UnLock()
			return
		stOne = self.m_hData[iId]
		if not stOne.has_key(iSession):
			self.UnLock()
			print("remove timer not found session=%d id=%d"%(iId,iSession))
			return
		stTimeNode = self.RemoveSession(iId,iSession)
		self.RemoveNode(stTimeNode)
		self.UnLock()

	#移除一个结点
	def RemoveNode(self,stTimeNode):
		if stTimeNode.m_stFront != None:
			stTimeNode.m_stFront.m_stNext = stTimeNode.m_stNext
		else:
			stTimeNode.m_stFather.m_stHead = stTimeNode.m_stNext

		if stTimeNode.m_stNext != None:
			stTimeNode.m_stNext.m_stFront = stTimeNode.m_stFront
		else:
			stTimeNode.m_stFather.m_stTail = stTimeNode.m_stFront	