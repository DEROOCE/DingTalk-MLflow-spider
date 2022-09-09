# DingTalk-MLflow-spider

**A simple practice on web spider.**

Functions:

* Scraping model training details from MLflow to DingTalk bots.

Directories:

* `single_task`: Dingtalk robot + MLflow monitoring for single training experiment.

* `multi_task`: Dingtalk robot + MLflow monitoring for multiple training experiments.

Code Structure:

* `msg_bot.py`: Dingtalk bot setting
* `spider.py`: web spider for MLflow monitoring url
* `run.py`: main file

Running:

```bash
python run.py
```

References:

* [DingTalkRobot-python](https://github.com/magician000/DingTalkRobot-python)
