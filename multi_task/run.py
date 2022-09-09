import time 
import datetime as dt

from msg_bot import DtalkRobot
from spider import post_request, extract_info

import requests
from requests.adapters import HTTPAdapter 
from urllib3.poolmanager import PoolManager
import ssl


class MyAdapter(HTTPAdapter):
    def init_poolmanager(self, connections, maxsize, block=False):
        self.poolmanager = PoolManager(num_pools=connections,
                                        maxsize=maxsize, 
                                        block=block,
                                        ssl_version=ssl.PROTOCOL_TLSv1)


def main():
    # webhook
    webhook = ""  # dingtalk robot webhook
    robot = DtalkRobot(webhook)
    url = ""  # mlflow url
    payload = {"experiment_ids":["5"]}    # 实验编号
    ids = ["5", "11", "12"]
    
    payloads = []
    for i in ids:
        payload = {"experiment_ids":[i]}
        payloads.append(payload)
    
    # train loss, eval loss , other metrics
    metrics = [["lm loss", "lm loss validation", "grad-norm"],
                ["train_loss", "validation_loss", "tflops"]]
    cnt = 0
    
    while True:
        text_before_l, data_before_l, text_after_l, data_after_l = [], [], [], []
        for payload, metric in zip(payloads, metrics):
            text_before = post_request(url, payload)
            data_before = extract_info(text_before, metric)
            text_before_l.append(text_before)
            data_before_l.append(data_before)
        
        time.sleep(10*60) # 10分钟检查一次是否有训练异常
        cnt += 1  # 10分钟计数
        cur_time = dt.datetime.now().strftime("%Y-%m-%d-%H时-%M分-%S秒")
        current = time.time()
        for payload, metric in zip(payloads, metrics):
            text_after = post_request(url, payload)
            data_after =  extract_info(text_after, metric)
            text_after_l.append(text_before)
            data_after_l.append(data_after)

        msg_info_list, msg_err_list, msg_run_list, msg_fail_list, msg_fin_list, exp_id_l = [], [], [],[],[],[]
        for dt_before, dt_after, metric in zip(data_before_l, data_after_l, metrics):
            error, finish, failed, run = [], [], [], []
            SAFE = True  # 定义训练是否异常的检测flag变量
            
            for before in dt_before[1]:
                for after in dt_after[1]:
                    if  (before[metric[0]] and before[metric[1]]) and (after[metric[0]] and after[metric[1]]):
                        if before["tags"] == after["tags"]:
                            loss_before = before[metric[0]]
                            loss_after = after[metric[0]]
                            eval_loss_before = before[metric[1]]
                            eval_loss_after = after[metric[1]]

                        
                            other_feat = []
                            for _ in metric[2:]:
                                #_before = before[_]
                                _after = after[_]
                                other_feat.append(_after)
                            
                            other_msg =  ""
                            for other, m in zip(other_feat, metric[2:]):
                                other_msg += f"; {m} = " + str(other)
                            #status_before = before["status"]
                            status_after = after["status"] 
                            end_time = after["end_time"]  # 结束时间
                            exp_id = after["experiment_id"]
                            
                            if  status_after == "RUNNING":
                                # 记录还在训练的模型
                                run_msg =  "\{ \"" + before["tags"] + "\" : lm loss = " + str(loss_after) + \
                                        "; lm loss validation =  " + str(eval_loss_after)  + \
                                        other_msg + "\} "
                                run.append(run_msg)
                                # 前后训练的loss相差小于1e-6, 且训练状态不是训练结束状态
                                #if abs(loss_after - loss_before) < 1e-5 and  abs(eval_loss_before - eval_loss_after) < 1e-6:
                                if abs(loss_before - loss_after) < 1e-6:
                                #if abs(eval_loss_before - eval_loss_after) < 1e-6:
                                    err_msg = before["tags"] + " 训练Loss开始不下降（可能是10分钟还未跑完一个step）\n"
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
            
            exp_id_l.append(exp_id)
            #if error or finish:
            if error:
                SAFE = False
                msg_err = ''
                for i in error:
                    msg_err += i    
            else:
                SAFE = True
                msg_err = "暂无出现训练异常的模型"
            msg_err_list.append(msg_err)
            
            if finish:
                msg_fin = ''
                for i in finish:
                    msg_fin += i
            else:
                msg_fin = '暂无训练结束的模型'
            msg_fin_list.append(msg_fin)
                
            if failed:
                msg_fail = ''
                for i in failed:
                    msg_fail += i
            else:
                msg_fail = '暂无训练失败的模型'
            msg_fail_list.append(msg_fail)
            
            if run:
                msg_run = ''
                for i in run:
                    msg_run += i
            else:
                msg_run = '暂无正在训练的模型'
            msg_run_list.append(msg_run)
            
            if not SAFE:
                message = "\n* ===================" +\
                    "\n* 警示信息: " +  msg_err +\
                    "\n* 实验ID：" + exp_id + \
                    "\n* 正在训练： " + msg_run  #+ "\n* 训练失败或终止(未超过2天): " + \
        
                msg_info_list.append([SAFE, message])
            
        info = ""
        
        # [SAFE, message]
        for msg in msg_info_list:
            safe = msg[0] 
            message = msg[1]
            if safe:
                pass 
            else:
                info += message
        if len(info)>0:
            try:
                STATUS = "GOOD"
                robot.sendMarkdown("训练类型", info)
            except:
                STATUS = "ERROR"
                time.sleep(30)
                robot.sendMarkdown("训练类型", info)
            finally:
                print(STATUS)
                        
        # 每次播报后休息1分钟    
        #time.sleep(10)
        time.sleep(60)
        
        print("cnt = ", cnt)
        if cnt % 6 == 0:  # 1小时播放一次 6
            case = ""
            for exp_id, msg_run, msg_err, msg_fail, msg_fin in zip(exp_id_l, msg_run_list, msg_err_list, msg_fail_list, msg_fin_list):
                case += "================" + \
                        "\n* 实验ID：" + exp_id + \
                        "\n* 正在训练：" +  msg_run + "\n* 训练异常: " + \
                                msg_err    + "\n* 训练失败或终止（未超过2天）: " + \
                                msg_fail   + "\n* 训练完成（未超过2天）：" + \
                                msg_fin 
                
            message = "## 模型训练检测情况" + "\n* 日志时间：" + cur_time + case

            
            try:
                STATUS = "GOOD"
                robot.sendMarkdown("训练类型", message)
            except:
                STATUS = "ERROR"
                time.sleep(30)
                robot.sendMarkdown("训练类型", message)
            finally:
                print(STATUS)

if __name__ == "__main__":
    """
    注意：对于不同的实验，需要改动参数的地方
    1. main()函数内， payloads编号修改, metrics监控的指标
    """
    s = requests.Session()
    s.mount('https://', MyAdapter())
    main()


