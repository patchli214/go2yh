cd /data/go2
nohup uwsgi --socket go2.sock --module go2.wsgi --chmod-socket=666 &
