#!/usr/bin/python
# coding=utf-8

import os
import TimeMgr
import random
import time

giAll   = 1001 
giCount = 0
gstTimeMgr = TimeMgr.TimeMgr()

class TimeCb():
	def __init__(self,iIndex):
		self.m_iLastTime = int(time.time()*1000)	
		self.m_iTime 	 = random.randint(1000,3000);
		self.m_iIndex    = iIndex
		self.m_iSession  = 0
	def run(self,szData):
		iCurTime = int(time.time()*1000)
		global giCount
		giCount = giCount + 1
		print("ID %d 时间%d 差%d session %d all %d"%(self.m_iIndex,self.m_iTime,iCurTime-self.m_iLastTime-self.m_iTime,self.m_iSession,giCount))
		self.m_iLastTime = iCurTime

		if gstTimeMgr.RemoveTimer(self.m_iSession) == False:
			print("remove error timerID %d session %d"%(self.m_iIndex,self.m_iSession))

if __name__ == '__main__':
	iTotal = 0
	gstTimeMgr.Display()
	print("----------start")
	for i in range(1,giAll):
		stTest = TimeCb(i)
		stTest.m_iSession = gstTimeMgr.AddTimer(stTest.run,stTest.m_iTime,True,None)
		iTotal = iTotal + 1
	print("---------------------%d"%(iTotal))
	gstTimeMgr.Display()
	while True:
		gstTimeMgr.UpdateTime()