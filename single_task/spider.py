from multiprocessing.sharedctypes import Value
import requests
import datetime as dt
import requests


def post_request(url, payload):
    response = requests.post(url, json=payload)
    print("status code = ", response.status_code)

    text = eval(response.text)
    return text 

def extract_info(text):
    """
    不同实验，设计的Loss名称不同
    loss名称需要自定义好
    """
    data_list = []
    num_runs = len(text["runs"])
    ins = []
    time = dt.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    for i in range(num_runs):
        data = {}
        
        # 添加过滤条件
        tag = text['runs'][i]['data']['tags'][0]["value"] + '-' + text["runs"][i]['data']['tags'][1]["value"] 
        if tag == "20220831105151-run_summarization.py":
            continue
        
        try:
            data["status"] = text["runs"][i]["info"]['status'] # 训练的状态
            data["experiment_id"] = text["runs"][i]["info"]["experiment_id"]
            data["tags"] = text['runs'][i]['data']['tags'][0]["value"] + '-' + text["runs"][i]['data']['tags'][1]["value"] 
            data["start_time"] = eval(str(text['runs'][i]['info']['start_time'])[:10]) # 前10位，精确到秒
        except:
            print("当前text解析失败")
            pass

        try:
            for j in text['runs'][i]['data']['metrics']:
                for key, value in j.items():
                    if value == "loss":
                        data['loss'] =  j["value"]
            
            assert data['loss'] 
        except:
            data['loss'] = None 
            pass
        try:
            for j in text['runs'][i]['data']['metrics']:
                for key, value in j.items():
                    if value == "tr_loss_step":
                        data["eval_loss"] = j["value"] 
                        
            assert data["eval_loss"]
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


if __name__ == '__main__':
    pass
