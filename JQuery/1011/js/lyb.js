$(function(){
	var num=1;//数字  用于累加
	//1.对按钮进行鼠标单击事件
	$("#btn").click(function(){
		// <p>用户+数字+说：+输入的字符串</p>
		//获取到输出的字符串后需要和div相关联  通过html方法进行转换
		var shuchu="<p>用户"+num+"说："+$("#text").val()+"</p>"+$("#box").html();
		//输出
		$("#box").html(shuchu);
		//优化
		num++;
		//发表完毕后将当前文本区域的内容清空
		$("#text").val("");
	});
});