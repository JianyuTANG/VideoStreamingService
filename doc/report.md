# RTP实验报告

唐建宇 2017012221



## 一、代码结构

```
Server/
	main.c           // 服务器入口
	server.h         // 公共头文件，声明所有函数和全局变量
	process.c        // 接受并分发不同请求
	ftp-commands.c   // 每个请求对应的处理函数
	file_operation.c // 处理文件操作的函数库
	utils.c          // 用到的其他函数
Client/
	main.py          // PyQt5程序入口及槽函数
	client.py        // 封装每一种任务的处理函数
	multi_thread.py  // 多线程类，实现非阻塞用
	dialog.py        // 弹出输入对话框类
	mainWindow.py    // 主界面ui
	inputDialog      // 弹出的对话框ui
```

