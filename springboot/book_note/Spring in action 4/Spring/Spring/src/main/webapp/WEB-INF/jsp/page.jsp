<%@ page language="java" contentType="text/html; charset=utf-8"
    pageEncoding="utf-8"%>
<%@ taglib uri="http://java.sun.com/jsp/jstl/core" prefix="c" %>
<%@ taglib uri="http://tiles.apache.org/tags-tiles" prefix="t"%> 
<html>
<body>
    <h2>Hello World! -- page.jsp</h2>
    <div><t:insertAttribute name="header"/></div>
    <div><t:insertAttribute name="body"/></div>
    <div><t:insertAttribute name="footer"/></div>
</body>
</html>
