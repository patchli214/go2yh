#* * * * * /data/go2/monitor.sh
port=80
nc -w2 localhost $port

if [ $? != 0 ];then
        echo '【'`date +"%Y-%m-%d %H:%M:%S"`'】检测到端口【'${port}'】已经关闭，该服务重新启动'>>/data/go2/log/monitor.log
        $(/data/go2/mysite.sh)
	exit
fi
echo