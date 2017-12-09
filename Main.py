#!/usr/bin/python
# coding=utf-8

import os
import TimeMgr
import WheelTimeMgr
import random
import time
import thread
import threading

g_All = 200000

class TimeCb():
	def __init__(self,iIndex):
		self.m_iLastTime = int(time.time()*1000)	
		self.m_iTime 	 = random.randint(100,100000);
		self.m_iIndex    = iIndex
		self.m_iSession  = iIndex

	def run(self,szData):
		iCurTime = int(time.time()*1000)
		print("ID=%d 时间=%d 差=%d session=%d"%(self.m_iIndex,self.m_iTime,iCurTime-self.m_iLastTime-self.m_iTime,self.m_iSession))
		self.m_iLastTime = iCurTime

#分级时间轮定时器
class LevelWheelTest(threading.Thread):
	def __init__(self):
		threading.Thread.__init__(self)

	def run(self):
		gstTimeMgr = WheelTimeMgr.WheelTimerMgr()
		for i in range(0,g_All):
			stTest = TimeCb(i+1)
			stNode = WheelTimeMgr.TimeNode(stTest.m_iTime,True)
			stNode.m_iSession = stTest.m_iSession
			stNode.m_fCb = stTest.run
			stNode.m_iId = 1
			gstTimeMgr.AddTimer(stNode)
		while True:
			gstTimeMgr.UpdateTime()
			time.sleep(0.0025)

#不分级定时器
class NoLevelTest(threading.Thread):
	def __init__(self):
		threading.Thread.__init__(self)

	def run(self):
		gstTimeMgr = TimeMgr.TimeMgr()
		for i in range(0,g_All):
			stTest = TimeCb(i+1)
			stTest.m_iSession = gstTimeMgr.AddTimer(stTest.run,stTest.m_iTime,True,None)
		while True:
			gstTimeMgr.UpdateTime()
			time.sleep(0.0025)

if __name__ == '__main__':
	random.seed(time.time())
	stNo    = NoLevelTest()
	stLevel = LevelWheelTest()
	stNo.start()
	stLevel.start()
	stNo.join()
	stLevel.join()