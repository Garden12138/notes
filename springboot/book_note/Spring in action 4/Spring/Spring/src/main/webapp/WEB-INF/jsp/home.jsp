<%@ page language="java" contentType="text/html; charset=utf-8"
    pageEncoding="utf-8"%>
<%@ taglib uri="http://java.sun.com/jsp/jstl/core" prefix="c" %>
<%@ taglib uri="http://tiles.apache.org/tags-tiles" prefix="t"%> 
<html>
<body>
    <h2>Hello World! -- homePage</h2>
    <c:if test="${data}!=null">
    <c:forEach items="${data}" var="da">
        <c:out value="${da.message}" />
    </c:forEach>
    </c:if>
    
    <c:out value="${params}" />
    <c:if test="${params==null}">
         <form action="http://192.168.23.5:8080/Spring/home/getFormParams" method="POST">
             id:<input type="text" name="id" /><br/>
             message:<input type="text" name="message" /><br/>
             time:<input type="text" name="time" /><br/>
             <input type="submit" value="commit" />
         </form>
    </c:if>
</body>
</html>
