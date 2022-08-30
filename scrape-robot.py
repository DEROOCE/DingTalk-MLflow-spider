#!/usr/bin/env python
# coding=utf-8
import time
import urllib
import json
import time
import requests
import urllib.response
import urllib.request
import urllib.parse
import datetime as dt
import requests

# 自定义机器人的封装类
class DtalkRobot(object):
    """docstring for DtRobot"""
    webhook = ""

    def __init__(self, webhook):
        super(DtalkRobot, self).__init__()
        self.webhook = webhook

    # text类型
    def sendText(self, msg, isAtAll=False, atMobiles=[]):
        data = {"msgtype": "text", "text": {"content": msg}, "at": {"atMobiles": atMobiles, "isAtAll": isAtAll}}
        return self.post(data)

    # markdown类型
    def sendMarkdown(self, title, text):
        data = {"msgtype": "markdown", "markdown": {"title": title, "text": text}}
        return self.post(data)

    # link类型
    def sendLink(self, title, text, messageUrl, picUrl=""):
        data = {"msgtype": "link", "link": {"text": text, "title": title, "picUrl": picUrl, "messageUrl": messageUrl}}
        return self.post(data)

    # ActionCard类型
    def sendActionCard(self, actionCard):
        data = actionCard.getData();
        return self.post(data)

    # FeedCard类型
    def sendFeedCard(self, links):
        data = {"feedCard": {"links": links}, "msgtype": "feedCard"}
        return self.post(data)

    def post(self, data):
        # post_data = json.JSONEncoder().encode(data)
        print(data)
        post_data = json.dumps(data).encode()
        req = urllib.request.Request(self.webhook, post_data)
        req.add_header('Content-Type', 'application/json')
        content = urllib.request.urlopen(req).read()
        print(content)
        return content


# ActionCard类型消息结构
class ActionCard(object):
    """docstring for ActionCard"""
    title = ""
    text = ""
    singleTitle = ""
    singleURL = ""
    btnOrientation = 0
    hideAvatar = 0
    btns = []

    def __init__(self, arg=""):
        super(ActionCard, self).__init__()
        self.arg = arg

    def putBtn(self, title, actionURL):
        self.btns.append({"title": title, "actionURL": actionURL})

    def getData(self):
        data = {"actionCard": {"title": self.title, "text": self.text, "hideAvatar": self.hideAvatar,
                               "btnOrientation": self.btnOrientation, "singleTitle": self.singleTitle,
                               "singleURL": self.singleURL, "btns": self.btns}, "msgtype": "actionCard"}
        return data


# FeedCard类型消息格式
class FeedLink(object):
    """docstring for FeedLink"""
    title = ""
    picUrl = ""
    messageUrl = ""

    def __init__(self, arg=""):
        super(FeedLink, self).__init__()
        self.arg = arg

    def getData(self):
        data = {"title": self.title, "picURL": self.picUrl, "messageURL": self.messageUrl}
        return data

def post_request(url, payload):
    """get the post content from web"""
    response = requests.post(url, json=payload)
    print("status code = ", response.status_code)

    text = eval(response.text)
    return text 

def extract_info(text):
    """
    不同实验，设计的Loss名称不同
    loss名称需要自定义
    """
    data_list = []
    num_runs = len(text["runs"])
    ins = []
    time = dt.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    for i in range(num_runs):
        data = {}
        try:
            data["status"] = text["runs"][i]["info"]['status'] # 训练的状态
            data["experiment_id"] = text["runs"][i]["info"]["experiment_id"]
            data["tags"] = text['runs'][i]['data']['tags']["value"] 
            data["start_time"] = eval(str(text['runs'][i]['info']['start_time'])[:10]) # 前10位，精确到秒
        except:
            print("当前text解析失败")
            pass

        try:
            data['loss'] = text['runs'][i]['data']['metrics']['loss']["value"]  # loss位置需要自己改动
        except:
            data['loss'] = None 
            pass
        try:
            data['eval_loss'] = text['runs'][i]['data']['metrics']['eval_loss']['value']
        except:
            data["eval_loss"] = None
        try:
            data["end_time"] = eval(str(text['runs'][i]['info']['end_time'])[:10])
        except:
            data["end_time"] = 0
            pass
        
        data_list.append(data)
        
    ins = [time, data_list]

    return ins
    
def main():
    # dingtalk  webhook
    webhook = "dingtalk webhook url here"
    # 公司群
    # webhook = 'h ttps://oapi.dingtalk.com/robot/send?access_token=c956a9143dd5fe81557558183529edaa379f6ae7939aa91d5a89051f8d3a3392'
    robot = DtalkRobot(webhook)
    url = "MLflow experiments monitoring web url here"
    payload = {"experiment_ids":["5"]}    # 实验编号
    
    cnt = 0
    
    while True:
        error = []
        finish = []
        failed = []
        run = []
        SAFE = True  # 定义训练是否异常的检测flag变量
        text_before = post_request(url, payload)
        data_before = extract_info(text_before)
        
        #time.sleep(20)  
        time.sleep(10*60) # 10分钟检查一次是否有训练异常
        cnt += 1  # 10分钟计数
        cur_time = dt.datetime.now().strftime("%Y-%m-%d-%H时-%M分-%S秒")
        current = time.time()
        text_after = post_request(url, payload)
        data_after =  extract_info(text_after)
        
        for before in data_before[1]:
            for after in data_after[1]:
                if  (before["loss"] and before["eval_loss"]) and (after["loss"] and after["eval_loss"]):
                    if before["tags"] == after["tags"]:
                        loss_before = before["loss"]
                        loss_after = after["loss"]
                        eval_loss_before = before["eval_loss"]
                        eval_loss_after = after["eval_loss"]
                        #status_before = before["status"]
                        status_after = after["status"] 
                        end_time = after["end_time"]  # 结束时间
                        
                        if  status_after == "RUNNING":
                            # 记录还在训练的模型
                            run_msg =  "\{ \"" + before["tags"] + "\" : Loss = " + str(loss_after) + \
                                    "; Eval Loss =  " + str(eval_loss_after) + '\} \n'
                            run.append(run_msg)
                            # 前后训练的loss相差小于1e-6, 且训练状态不是训练结束状态
                            if abs(loss_after - loss_before) < 1e-5 or  abs(eval_loss_before - eval_loss_after) < 1e-6:
                                err_msg = before["tags"] + " 训练Loss开始不下降\n"
                                error.append(err_msg)
                            # 前后训练的loss突增
                            if loss_after >= loss_before * 10 or eval_loss_after >= eval_loss_before * 10:
                                err_msg = before["tags"] + " 训练Loss突增10倍以上\n"
                                error.append(err_msg)
                        
                        if status_after == "FAILED":
                        # if after["status"] == "FAILED" and  before["status"] == "RUNNING":
                            # 训练异常结束超过2天，不显示
                            if abs(current - end_time) > (60*60*24*2):
                                failed_msg = ''
                            else:
                                failed_msg = before["tags"] + " 训练失败或终止\n"
                            failed.append(failed_msg)
                        
                        if status_after == "FINISHED":
                            if abs(current - end_time)  >  (60*60*24*2) :
                                # 正常结束超过2天，不再显示
                                finish_msg = ''
                            else:
                                finish_msg = before["tags"] + " 训练结束\n"
                            finish.append(finish_msg) 
                            
        #if error or finish:
        if error:
            SAFE = False
            msg_err = ''
            for i in error:
                msg_err += i    
        else:
            SAFE = True
            msg_err = "暂无出现训练异常的模型"

        if finish:
            msg_fin = ''
            for i in finish:
                msg_fin += i
        else:
            msg_fin = '暂无训练结束的模型'
            
        if failed:
            msg_fail = ''
            for i in failed:
                msg_fail += i
        else:
            msg_fail = '暂无训练失败的模型'

        if run:
            msg_run = ''
            for i in run:
                msg_run += i
        else:
            msg_run = '暂无正在训练的模型'
        
        if not SAFE:
            message = "## CPM训练信息  \n* 错误信息: " +  msg_err +\
                "\n* 正在训练： " + msg_run + "\n* 训练失败或终止(未超过2天): " + \
                        msg_fail   + "\n* 训练完成（未超过2天）：" + \
                        msg_fin
            robot.sendMarkdown("训练类型", message)
    
                        
        # 每次播报后休息1分钟    
        time.sleep(60)
        
        if cnt % 1 == 0:  # 1小时播放一次 6
            message = "## CPM训练情况" + "\n* 日志时间：" + cur_time +\
                                        "\n* 正在训练：" +  msg_run + "\n* 训练异常: " + \
                                                msg_err    + "\n* 训练失败或终止（未超过2天）: " + \
                                                msg_fail   + "\n* 训练完成（未超过2天）：" + \
                                                msg_fin 
            robot.sendMarkdown("训练类型", message)
            

if __name__ == "__main__":
    """
    注意：对于不同的实验，需要改动参数的地方
    1. main()函数内， payload = {"experiment_ids":["5"]} , 编号修改
    2. extract_info()函数中，需要根据具体实验的metrics设置来更换
    """
    main()

