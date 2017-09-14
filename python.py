#!/usr/bin/python
# coding=utf-8

import os
import TimeMgr

class TimeCb():
	def __init__(self):
		self.m_num = 10086	
	def run(self,szData):
		print("1秒回调")

if __name__ == '__main__':
	stTimeMgr = TimeMgr.TimeMgr()
	stTest = TimeCb()
	stTimeMgr.AddTime(stTest.run,1000,True,None)
	while True :
		stTimeMgr.UpdateTime()