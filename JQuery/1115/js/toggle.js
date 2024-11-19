$(document).ready(function(){
		$("#flag").mouseover(function(){
			if($("#menu").is(':hidden')){   // 判断菜单是否为隐藏状态
				$("#menu").show(300);		// 如果隐藏，则将菜单显示
			}
		});
		$("#menu").hover(null,function(){
			$("#menu").hide(300);		//隐藏菜单
		});		
	});