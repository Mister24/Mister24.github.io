---
title: 路由网关 —— Zuul
date: 2019-06-20 21:28:45
tags:
  - 微服务
  - springcloud
---
&nbsp;&nbsp;微服务网关涉及到负载均衡，缓存，路由，访问控制，服务代理，监控，日志等功能，
# 1. zuul的功能
&nbsp;&nbsp;zuul的主要功能如下：
- 动态路由和负载均衡；
- 统一api的暴露，屏蔽内部服务敏感信息；
- 身份认证和权限认证，安全保护；
- 监控及日志输出，记录请求；
- 流量监控，服务降级；
- api接口从内部服务分离，方便测试。
---
# 2. zuul的工作原理
&nbsp;&nbsp;zuul通过自定义的ZuulServlet对请求进行控制，通过一系列的过滤器，在http请求的发起和响应期间进行一系列的操作。zuul采用动态读取、编译和运行这些过滤器，这些过滤器之间不能互相直接通信，而是使用RequestContext对象来共享数据，每个请求都会创建一个RequestContext。
&nbsp;&nbsp;zuul在2.0版本对于现有框架进行了升级，使用了netty的nio机制提升性能，但是官方给出的性能提升数据大致在20%，所以如果不是异步场景较多，仍然考虑采用1.0版本，本文仍然以1.0版本为例。
![](photos/zuul-1.png)
&nbsp;&nbsp;外部http请求到达api网关服务的时候，首先它会进入第一个阶段pre，在这里它会被pre类型的过滤器进行处理。该类型过滤器的主要目的是在进行请求路由之前做一些前置加工，比如请求的校验等。
&nbsp;&nbsp;在完成了pre类型的过滤器处理之后，请求进入第二个阶段routing，也就是之前说的路由请求转发阶段，请求将会被routing类型的处理器处理。这里的具体处理内容就是将外部请求转发到具体服务实例上去的过程,
&nbsp;&nbsp;当服务实例请求结果都返回之后，routing阶段完成，请求进入第三个阶段post。此时请求将会被post类型的过滤器处理，这些过滤器在处理的时候不仅可以获取到请求信息，还能获取到服务实例的返回信息，所以在post类型的过滤器中，我们可以对处理结果进行一些加工或转换等内容。
&nbsp;&nbsp;还有一个特殊的阶段error，该阶段只有在上述三个阶段中发生异常的时候才会触发，但是它的最后流向还是post类型的过滤器，因为它需要通过post过滤器将最终结果返回给请求客户端（对于error过滤器的处理，在spring cloud zuul的过滤链中实际上有一些不同）
![](photos/zuul-2.png)
&nbsp;&nbsp;zuul2.0前端用Netty Server代替Servlet，目的是支持前端异步。后端用Netty Client代替Http Client，目的是支持后端异步，过滤器换了名字，用Inbound Filters代替Pre-routing Filters，用Endpoint Filter代替Routing Filter，用Outbound Filters代替Post-routing Filters。

---
# 3. 实例分析
 ## 3.1 新增依赖
&nbsp;&nbsp;需要引入Eureka Client的依赖和zuul的依赖。
```xml
<dependency>
    <groupId>org.springframework.cloud</groupId>
    <artifactId>spring-cloud-starter-netflix-eureka-client</artifactId>
</dependency>
<dependency>
    <groupId>org.springframework.cloud</groupId>
    <artifactId>spring-cloud-starter-netflix-zuul</artifactId>
</dependency>
```
 ## 3.2 注解引入
&nbsp;&nbsp;zuul的注解为@EnableZuulProxy，用来开启Zuul的功能。
 ## 3.3 配置数据
- eureka的配置
- zuul的路由配置
&nbsp;&nbsp;需要加入path和serviceId属性，满足path规则的请求都会被转发到对应serviceId的服务。

## 3.4 请求调用
```xml
zuul.routes.hiapi.path=/hiapi/**
zuul.routes.hiapi.service-id=eureka-client
```
&nbsp;&nbsp;使用上述规则，会将请求转发到eureka-client这个服务上，同时我们在自定义的filter中对token参数进行了校验。
```java
@Component
public class MyFilter extends ZuulFilter {
    /** logger */
    private static final Logger logger = LoggerFactory.getLogger(MyFilter.class);

    // 过滤器类型，这里是前置过滤
    @Override
    public String filterType() {
        return PRE_TYPE;
    }

    // 优先级，数值越低，优先级越高
    @Override
    public int filterOrder() {
        return 0;
    }

    // 只有这里为true，才会执行过滤规则
    @Override
    public boolean shouldFilter() {
        return true;
    }

    @Override
    public Object run() throws ZuulException {
        RequestContext context = RequestContext.getCurrentContext();
        HttpServletRequest request = context.getRequest();
        Object accessToken = request.getParameter("token");
        if (accessToken == null) {
            logger.warn("token is empty.");
            context.setSendZuulResponse(false);
            context.setResponseStatusCode(401);
            try {
                context.getResponse().getWriter().write("token is empty.");
            } catch (Exception e) {
                return null;
            }
            logger.info("ok");
        }
        return null;
    }
}

```
无token
![](photos/zuul4.png)
有token但超时，需要增加timeout的配置。
![](photos/zuul5.png)

---
# 4. 原理剖析
 ## 4.1 过滤器
&nbsp;&nbsp;通过shouldFilter()指定是否开启过滤器，如果是run()方法中的过滤器逻辑才会生效；通过filterType()指定过滤器类型；通过filterOrder()指定过滤顺序，值越小，优先级越高；通过重写run()来实现真实的过滤逻辑。
filterType
- pre过滤器
&nbsp;&nbsp;可以进行一些权限认证，日志记录，或者额外给Request增加一些属性供后续的filter使用。pre会优先按照order从小到大执行，然后再去执行请求转发到业务服务；
- routing过滤器
- post过滤器
&nbsp;&nbsp;在post的filter里，一般做一些日志记录，或者额外增加response属性；
- error过滤器
&nbsp;&nbsp;对于同一种类型的过滤器，可以通过设置不同的优先级来定义生效的时机，比如说在pre过滤器中可以有两个自定义的过滤器，只需要设置filterOrder为0和1即可控制生效的先后顺序。

参考
https://blog.csdn.net/j3T9Z7H/article/details/81025180