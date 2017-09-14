#!/usr/bin/python
# coding=utf-8

import time

TIMER_LIST_NR   = 256  
TIMER_LIST_MASK = 255 

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
	def Reset(self):
		self.m_stNext 		= None
		self.m_stFront  	= None
		self.m_iExpireTick  = 0
		self.m_iSession 	= 0

class TimeLink:
	def __init__(self):
		self.m_stHead = None
		self.m_stTail = None

#----------定时器-----------
class TimeMgr:
	def __init__(self):
		self.m_iSession  = 1
		self.m_szData    = []
		self.m_iCurTick  = self.GetCurTick()
		self.m_hData	 = {}
		for i in range(1,TIMER_LIST_NR+1):
			self.m_szData.append(TimeLink())

	def GetCurTick(self):
		return int(round(time.time() * 100))

	def HashCode(self,iExpireTick):
		return TIMER_LIST_MASK & iExpireTick

	#单位毫秒
	def AddTime(self,fFunCb,iTime,bIsLoop,stData):
		iExpireTick = self.GetTick(iTime) + self.m_iCurTick
		iCurSession = self.GetSession()
		stTimeNode  = TimeNode(fFunCb,iExpireTick,iTime,bIsLoop,stData,iCurSession)

		self.AddNode(stTimeNode)

		return iCurSession

	def AddNode(self,stTimeNode):
		iIndex 		= self.HashCode(stTimeNode.m_iExpireTick)
		stTimeLink  = self.m_szData[iIndex]

		if stTimeLink.m_stHead == None:
			stTimeLink.m_stHead = stTimeNode
			stTimeLink.m_stTail = stTimeNode
		else:
			stTimeNode.m_stFront = stTimeLink.m_stTail
			stTimeLink.m_stNext  = stTimeNode
			stTimeLink.m_stTail  = stTimeNode

		self.m_hData[stTimeNode.m_iSession] = stTimeNode

	def GetTick(self,iTime):
		return iTime/10

	def GetSession(self):
		if self.m_iSession >= 4294967295:
			self.m_iSession = 1
		iResultSession  = self.m_iSession
		self.m_iSession = self.m_iSession + 1
		return iResultSession

	#定时更新
	def UpdateTime(self):
		iCurTick = self.GetCurTick()
		iTickCount = iCurTick - self.m_iCurTick
		if iTickCount < 1:
			return
		self.m_iCurTick = iCurTick 
		stLoopNode = []
		for i in range(1,iTickCount+1):
			self.m_iCurTick = self.m_iCurTick+1
			iIndex = self.HashCode(self.m_iCurTick)
			stTimeLink = self.m_szData[iIndex]
			self.TimeExecute(stTimeLink,stLoopNode)

		for k,v in enumerate(stLoopNode):
			v.m_iExpireTick  = self.GetTick(v.m_iTime) + self.m_iCurTick
			v.m_iSession 	 = self.GetSession()
			self.AddNode(v)

	def TimeExecute(self,stTimeLink,stLoopNode):
		stCurNode  = stTimeLink.m_stHead
		stTempNode = None
		while stCurNode != None:
			if self.m_iCurTick == stCurNode.m_iExpireTick:
				stCurNode.m_fFunCb(stCurNode.m_stData)
				stTempNode = stCurNode
				if stCurNode.m_stFront != None:
					stCurNode.m_stFront.m_stNext = stCurNode.m_stNext
				else:
					stTimeLink.m_stHead = stCurNode.m_stNext

				if stCurNode.m_stNext != None:
					stCurNode.m_stNext.m_stFront = stCurNode.m_stFront

				stCurNode = stCurNode.m_stNext

				stTempNode.Reset()
				if stTempNode.m_bIsLoop:
					stTempNode.Reset()
					stLoopNode.append(stTempNode)

		if stTimeLink.m_stHead == None:
			stTimeLink.m_stTail = None