---
title: 负载均衡 —— Ribbon
date: 2019-06-07 21:29:42
categories: 
  - springcloud
tags:
  - 微服务
  - springcloud
---

# 负载均衡

&nbsp;&nbsp;负载均衡是指将负载分摊到多个执行单元上，常见的有2种方式：

- 独立进程单元，通过负载均衡策略，将请求转发到不同的执行单元，如Nginx；
- 将负载均衡逻辑以代码形式封装在服务消费者的客户端上，客户端维护一份服务提供者的信息列表，通过负载均衡策略将请求分摊给多个服务提供者，从而达到负载均衡的目的，如Ribbon。

---
# Ribbon的策略
&nbsp;&nbsp;Ribbon使用的是客户端的负载均衡策略，两种方式：

- Ribbon + RestTemplate
- Ribbon + Feign

---
# RestTemplate + Ribbon消费服务

&nbsp;&nbsp;Ribbon中负载均衡的客户端为LoadBalancerClient，在Spring Cloud项目中，Ribbon默认从Eureka Client的服务注册列表中获取服务的信息并保存，然后通过LoadBalancerClient来选择不同的服务实例从而实现负载均衡。如果不希望使用Eureka的注册信息，可以自己维护一份注册列表，然后利用Ribbon实现负载均衡。

---
# 源码分析

&nbsp;&nbsp;LoadBalancerClient接口继承自ServiceInstanceChooser，实现类为RibbonLoadBalancerClient。

![](photos/image.png)

重要的方法如下：

```java
<T> T execute(String serviceId, LoadBalancerRequest<T> request) **throws** IOException;

<T> T execute(String serviceId, ServiceInstance serviceInstance, LoadBalancerRequest<T> request) **throws** IOException;

ServiceInstance choose(String serviceId);
```
&nbsp;&nbsp;这个方法是用来选择具体的服务实例，最终委托给ILoadBalancer的chooseServer(Object key)方法去选择具体的服务实例。
![](photos/image1.png)

---
# 负载均衡策略
&nbsp;&nbsp;IRule用于配置负载均衡策略，其中的choose()方法是根据key来获取server的实例。IRule中默认包含了7种负载均衡策略。
![](photos/image2.png)
- RoundRobinRule 【轮询】
&nbsp;&nbsp;默认尝试10次
- RandomRule 【随机】
- AvailabilityFilteringRule  【可用过滤】
&nbsp;&nbsp;会先过滤掉由于多次访问故障而处于断路器跳闸状态的服务，还有并发的连接数超过阈值的服务，然后对剩余的服务列表进行轮询
- WeightedResponseTimeRule 【响应时间权重】
&nbsp;&nbsp;根据平均响应时间计算所有服务的权重，响应时间越快服务权重越大被选中的概率越高。刚启动时，如果统计信息不足，则使用轮询策略，等信息足够，切换到 WeightedResponseTimeRule
- RetryRule 【在选定负载均衡策略上使用轮询的方式重试】
&nbsp;&nbsp;先按照轮询策略获取服务，如果获取失败则在指定时间内重试，获取可用服务
- BestAvailableRule 【选择最小请求数的服务器】
&nbsp;&nbsp;选过滤掉多次访问故障而处于断路器跳闸状态的服务，然后选择一个并发量最小的服务，如果没找到，使用随机轮询策略选取；
- ZoneAvoidanceRule （默认） 【根据服务器所属服务区的整体运行状况来轮询选择】
&nbsp;&nbsp;符合判断server所在区域的性能和server的可用性选择服务，根据服务器所属服务区的运行状况和可用性来进行负载均衡。

---
# IPing
&nbsp;&nbsp;IPing向server发送"ping"，根据是否有回应来判断server是否可用。
![](photos/image3.png)
实现类共有5种：
- DummyPing
&nbsp;&nbsp;直接返回true
- NIWSDiscoveryPing
&nbsp;&nbsp;根据DiscoveryEnabledServer的InstanceInfo的status进行判断，如果为UP，表明可用；
- NoOpPing
&nbsp;&nbsp;不真实ping，直接返回true；
- PingConstant
&nbsp;&nbsp;固定返回某服务是否可用，是一个常量值；
- PingUrl
&nbsp;&nbsp;使用HttpClient进行ping操作，根据返回结果判定是否可用。
负载均衡器从Eureka Client获取服务列表信息，并根据IRule的策略进行路由，根据IPing判断服务的可用性。
```java
private List<DiscoveryEnabledServer> obtainServersViaDiscovery() {
    List<DiscoveryEnabledServer> serverList = new ArrayList<DiscoveryEnabledServer>();

    if (eurekaClientProvider == null || eurekaClientProvider.get() == null) {
        logger.warn("EurekaClient has not been initialized yet, returning an empty list");
        return new ArrayList<DiscoveryEnabledServer>();
    }

    EurekaClient eurekaClient = eurekaClientProvider.get();
    if (vipAddresses!=null){
        for (String vipAddress : vipAddresses.split(",")) {
            // if targetRegion is null, it will be interpreted as the same region of client
            List<InstanceInfo> listOfInstanceInfo = eurekaClient.getInstancesByVipAddress(vipAddress, isSecure, targetRegion);
            for (InstanceInfo ii : listOfInstanceInfo) {
                if (ii.getStatus().equals(InstanceStatus.UP)) {

                    if(shouldUseOverridePort){
                        if(logger.isDebugEnabled()){
                            logger.debug("Overriding port on client name: " + clientName + " to " + overridePort);
                        }

                        // copy is necessary since the InstanceInfo builder just uses the original reference,
                        // and we don't want to corrupt the global eureka copy of the object which may be
                        // used by other clients in our system
                        InstanceInfo copy = new InstanceInfo(ii);

                        if(isSecure){
                            ii = new InstanceInfo.Builder(copy).setSecurePort(overridePort).build();
                        }else{
                            ii = new InstanceInfo.Builder(copy).setPort(overridePort).build();
                        }
                    }

                    DiscoveryEnabledServer des = createServer(ii, isSecure, shouldUseIpAddr);
                    serverList.add(des);
                }
            }
            if (serverList.size()>0 && prioritizeVipAddressBasedServers){
                break; // if the current vipAddress has servers, we dont use subsequent vipAddress based servers
            }
        }
    }
    return serverList;
}
```
&nbsp;&nbsp;对于ribbon从Eureka Client获取注册信息，由于服务可能存在更新，所以需要定时从Eureka Client获取最新的注册信息。
```java
void setupPingTask() {
    if (canSkipPing()) {
        return;
    }
    if (lbTimer != null) {
        lbTimer.cancel();
    }
    lbTimer = new ShutdownEnabledTimer("NFLoadBalancer-PingTimer-" + name, true);
    lbTimer.schedule(new PingTask(), 0, pingIntervalSeconds * 1000);
    forceQuickPing();
}
```
&nbsp;&nbsp;在setupPingTask()方法中，开启了shutdownEnableTimer的PingTask任务，默认情况下，变量pingIntervalSeconds的值为10，即每10秒向Eureka Client发送一次心跳“ping”。在PingTask中创建了一个Pinger对象，并执行了runPinger()方法。
```java
class PingTask extends TimerTask {
    public void run() {
        try {
           new Pinger(pingStrategy).runPinger();
        } catch (Exception e) {
            logger.error("LoadBalancer [{}]: Error pinging", name, e);
        }
    }
}
```
&nbsp;&nbsp;在LoadBalancerAutoConfiguration类中，首先维护了一个被LoadBalanced修饰的RestTemplate对象的list。初始化过程中，通过调用customer.customize(restTemplate)方法给RestTemplate增加拦截器LoadBalancerInterceptor，LoadBalancerInterceptor用于实时拦截，在LoadBalancerInterceptor中实现了负载均衡的方法。
```java
public ClientHttpResponse intercept(final HttpRequest request, final byte[] body,
      final ClientHttpRequestExecution execution) throws IOException {
   final URI originalUri = request.getURI();
   String serviceName = originalUri.getHost();
   Assert.state(serviceName != null,
         "Request URI does not contain a valid hostname: " + originalUri);
   return this.loadBalancer.execute(serviceName,
         this.requestFactory.createRequest(request, body, execution));
}
```

---
# 结论
&nbsp;&nbsp;Ribbon的负载均衡主要通过LoadBalancerClient来实现，而具体实现交给ILoadBalancer处理，ILoadBalancer通过配置IRule、IPing等，向Eureka Client获取注册列表信息，默认每10s向Eureka Client发送一次“ping”来检查是否需要更新服务的注册列表信息，最后在得到的服务列表的就出上，ILoadBalancer根据IRule的规则进行负载均衡。
&nbsp;&nbsp;RestTemplate加上@LoadBalance注解之后，在远程调度的时候可以实现负载均衡，主要是维护了一个被@LoadBalance注解的RestTemplate列表，为该列表加上拦截器，在拦截器的方法中，将远程调度方法交给Ribbon的负载均衡器ILoadBalancerClient去处理，从而达到负载均衡的目的。
