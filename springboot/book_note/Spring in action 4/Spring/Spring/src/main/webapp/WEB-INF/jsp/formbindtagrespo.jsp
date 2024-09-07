<%@ page language="java" contentType="text/html; charset=utf-8"
    pageEncoding="utf-8"%>
<%@ taglib uri="http://www.springframework.org/tags/form" prefix="sf" %>
<%@ taglib uri="http://java.sun.com/jsp/jstl/core" prefix="c" %>
<html>
<body>
    <h2>表单绑定标签库</h2>
    <c:if test="${params!=null}">
    <sf:form action="http://192.168.23.5:8080/Spring/home/getFormParamsByFormBindTagRespo" method="POST" commandName="params">
        id:<sf:input path="id"/></br>
        message:<sf:input path="message"/></br>
        time:<sf:input path="time"/></br>
        <input type="submit" value="commit" />
    </sf:form>
    </c:if>
</body>
</html>
