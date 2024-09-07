<%@ page language="java" contentType="text/html; charset=utf-8"
    pageEncoding="utf-8"%>
<%@ taglib uri="http://www.springframework.org/tags" prefix="s" %>
<%@ taglib uri="http://java.sun.com/jsp/jstl/core" prefix="c" %>
<!DOCTYPE html>
<html>
<head>
</head>
<body>
    <h2>通用标签库</h2>
    <h3>国际化信息应用</h3>
    <s:message code="spring4.username"/>
    <h3>创建URL应用</h3>
    <a href="<s:url value="/home/show" />">直接渲染响应跳转至home.jsp</a></br>
    <s:url value="/home/show" var="jumpHome"/>
    <a href="${jumpHome}">先赋值变量再渲染响应跳转至home.jsp</a></br>
    <s:url value="/home/getQueryParams" var="jumpHomeByQueryParams">
       <s:param name="max" value="10" />
       <s:param name="count" value="10" />
    </s:url>
    <a href="${jumpHomeByQueryParams}">通过查询参数跳转值home.jsp</a></br>
    <s:url value="/home/getPathParams/{max}/{count}" var="jumpHomeByPathParams">
       <s:param name="max" value="11" />
       <s:param name="count" value="11" />
    </s:url>
    <a href="${jumpHomeByPathParams}">通过路径参数跳转值home.jsp</a></br>
    <span>将URL转义成html字符串输出<s:url value="/home/getFormParams" htmlEscape="true" /></span></br>
    <s:url value="/home/getFormParams" javaScriptEscape="true" var="jsEscape"/>
    <button id="jsEscapeBtn" type="submit" onclick="show()">将URL转义成js字符串弹框输出</button></br>
    <script type="text/javascript">
    function show(){
    	var jsEscape = "${jsEscape}";
    	alert("${jsEscape}");
    }
    </script>
    <h3>转义内容应用</h3>
    <s:escapeBody htmlEscape="true">
    <span>将URL转义成html字符串输出</span>
    </s:escapeBody>
    </br>
    <s:escapeBody javaScriptEscape="true">
    <span>将URL转义成js字符串弹框输出</span>
    </s:escapeBody>
</body>
</html>
