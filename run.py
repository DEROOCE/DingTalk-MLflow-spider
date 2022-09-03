import time 
import datetime as dt

from msg_bot import DtalkRobot
from spider import post_request, extract_info

def main():
    webhook = ""  # dingtalk webhook url here
    robot = DtalkRobot(webhook)
    url = ""     # MLflow experiment monitoring web url here
    payload = {"experiment_ids":["1"]}    # 实验编号
    
    cnt = 0
    
    while True:
        error = []
        finish = []
        failed = []
        run = []
        SAFE = True  # 定义训练是否异常的检测flag变量
        text_before = post_request(url, payload)
        data_before = extract_info(text_before)
        
        #time.sleep(5)  
        time.sleep(10*60) # 10分钟检查一次是否有训练异常
        cnt += 1  # 10分钟计数
        cur_time = dt.datetime.now().strftime("%Y-%m-%d-%H时-%M分-%S秒")
        current = time.time()
        text_after = post_request(url, payload)
        data_after =  extract_info(text_after)
        
        for before in data_before[1]:
            for after in data_after[1]:
                if  (before['loss'] and before["eval_loss"]) and (after['loss'] and after["eval_loss"]):
                    if before["tags"] == after["tags"]:
                        loss_before = before["loss"]
                        loss_after = after["loss"]
                        eval_loss_before = before["eval_loss"]
                        eval_loss_after = after["eval_loss"]
                        #status_before = before["status"]
                        status_after = after["status"] 
                        end_time = after["end_time"]  # 结束时间
                        exp_id = after["experiment_id"]
                        
                        if  status_after == "RUNNING":
                            # 记录还在训练的模型
                            run_msg =  "\{ \"" + before["tags"] + "\" : Loss = " + str(loss_after) + \
                                    "; tr_Loss_step =  " + str(eval_loss_after) + '\} \n'
                            run.append(run_msg)
                            # 前后训练的loss相差小于1e-6, 且训练状态不是训练结束状态
                            #if abs(loss_after - loss_before) < 1e-5 and  abs(eval_loss_before - eval_loss_after) < 1e-6:
                            if abs(eval_loss_before - eval_loss_after) < 1e-6:
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
            message = "## 模型训练检测信息（每10分钟检测一次）  \n* 警示信息: " +  msg_err +\
                "\n* 实验ID：" + exp_id + \
                "\n* 正在训练： " + msg_run  #+ "\n* 训练失败或终止(未超过2天): " + \
                        #msg_fail   + "\n* 训练完成（未超过2天）：" + \
                        #msg_fin

            #  If meet a error, then retry
            try:
                STATUS = "GOOD"
                robot.sendMarkdown("训练类型", message)
            except:
                STATUS = "ERROR"
                time.sleep(30)
                robot.sendMarkdown("训练类型", message)
            finally:
                print(STATUS)
                        
        # 每次播报后休息1分钟    
        #time.sleep(10)
        time.sleep(60)
        
        print("cnt = ", cnt)
        if cnt % 6 == 0:  # 1小时播放一次 6
            message = "## 模型训练检测情况" + "\n* 日志时间：" + cur_time +\
                                        "\n* 实验ID：" + exp_id + \
                                        "\n* 正在训练：" +  msg_run + "\n* 训练异常: " + \
                                                msg_err    + "\n* 训练失败或终止（未超过2天）: " + \
                                                msg_fail   + "\n* 训练完成（未超过2天）：" + \
                                                msg_fin 
            
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
    1. main()函数内， payload = {"experiment_ids":["5"]} , 编号修改
    2. extract_info()函数中，需要根据具体实验的metrics设置来更换
    """
    main()


