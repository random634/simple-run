## SimpleRun
简单运行任务、记录执行结果

### Server
- sanic

### Client
- vue
- layui-vue

### Run
```
  # env prepare
  python3 -m pip install pipenv
  python3 -m pipenv install

  # run
  python3 -m pipenv shell
  python3 ./server.py
```

### Todos
- [ ] 新建任务
  - [X] 参数化-字符串参数（名称、描述、默认值）
  - [X] 参数化-布尔参数（名称、描述、默认值）
  - [X] 参数化-选项参数（名称、描述、默认值、选项）
  - [ ] 参数化-脚本控制参数
  - [X] 任务描述
  - [X] 任务保存
  - [X] 任务表现
  - [X] 添加参数页面
- [X] 编辑任务
- [X] 执行任务
- [X] 执行记录
  - [ ] 执行记录动态刷新