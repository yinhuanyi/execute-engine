#!/bin/bash

TEST_DIR=/app/fil-execute-engine

if  [ $# -lt 1 ];then
    echo "Please Input A Argument"
    exit 1
fi

if [ -z $CURRENT_DIR ]; then
    CURRENT_DIR=`pwd`
fi


REQUEIRMENTS=$CURRENT_DIR/requirements.txt
AGENT_PID=$CURRENT_DIR/engine.pid


function init_env(){
    # 安装依赖
    apt install -y python3-pip python3-dev nfs-common
    pip3 install -r $REQUEIRMENTS
    # 挂载nfs, IP是nfs的地址
    echo "$CURRENT_DIR" >> $TEST_DIR/dir.log
    DISTRIBUTE_IP=`awk -F " = " '/DISTRIBUTE/{print $2}' $CURRENT_DIR/conf/server.conf`
    echo "$DISTRIBUTE_IP" >> $TEST_DIR/dir.log
    mount -t nfs $DISTRIBUTE_IP:/app/fil-distribute/data/files /mnt
}

function clean_env() {
    # 卸载/mnt
    umount /mnt
}

# 启动agent
case $1 in

start)
    init_env
    python3  $CURRENT_DIR/manager.py start
    ;;

stop)
    python3  $CURRENT_DIR/manager.py stop
    clean_env
    ;;

restart)
    python3  $CURRENT_DIR/manager.py stop
    clean_env
    sleep 2
    init_env
    python3  $CURRENT_DIR/manager.py start
    ;;

status)
    if [ -f $AGENT_PID ]; then
      echo "Engine Is Running......"
    else
      echo "Engine Is Not Running......"
    fi
    ;;

*)
    echo "Usage: bash control.sh {start|stop|restart|status}"
    exit 1 ;;

esac