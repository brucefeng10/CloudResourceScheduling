# Cloud Resource Scheduling
### 阿里巴巴天池算法竞赛（2018）：[阿里巴巴全球调度算法大赛](https://tianchi.aliyun.com/competition/entrance/231663/introduction)

初赛：整数规划+列生成算法尝试

## 赛题简单说明：
> 有一些instance，这些instance分为若干类，每一类的instance属性相同，需要将这些instance放到若干宿主机（machine）上，使得目标函数值最小，同时满足以下约束：
>* 每个实例都标明了CPU、memory、disk此3个维度的资源需求，其中CPU、memory以分时占用曲线的形式给出，在任意时刻，任意一个宿主机A上，所有部署在宿主机A上的实例的任意资源都不能超过宿主机A的该资源容量;
>* 另外还有P、M、PM三类资源，定义了应用实例的重要程度，任意一台宿主机上的部署数目不能超过该类型宿主机能够容纳的重要应用数目上限;
>* 混部集群时刻处于复杂的干扰环境中，所以我们需要满足一些规避干扰约束，一条规避干扰约束被描述为<APP_A, APP_B, k>，代表若一台宿主机上存在APP_A类型的实例，则最多能部署k个APP_B类型的实例。注意，k可能为0。APP_A和APP_B也可能代表同一个APP（e.g. <APP_A, APP_A, k>），代表同一台机器上最多可以部署的该APP的实例的数目.

> 目标函数: (用整数规划的时候对该目标函数进行了线性转换，近似拟合)
>* ![](https://github.com/brucefeng10/CloudResourceScheduling/blob/master/resources/score-criteria.jpg)


数据观察(a版)：  
instance: 总共68219个，分为9338类，相同类的instance属性一样；  
app: 总共9338个（类），每种类型app有若干个instance，总共68219个instance；  
machine: 总共6000台，可分为大小两种型号，每种型号各一半；  

