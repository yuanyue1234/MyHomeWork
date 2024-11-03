$(document).ready(function(){
	/**导航头部我的当当 显示二级菜单 绑定悬浮 bind一个事件*
    $(".on").bind("mouseover",function(){
		$(".topDown").show();
	});*/

    /**bind 两个事件**/
    //  $(".top-m .on").bind({
	// 	mouseover:function(){
	// 		$(".topDown").show();
	// 	},
	// 	mouseout:function(){
	// 		$(".topDown").hide();
	// 	}
    // });
    
    $(".top-m .on").hover(function(){
        $(".topDown").show("slow");
    },
    function(){
        $(".topDown").hide("fast");
    }
    );
 
    	/**主菜单鼠标移上时背景颜色加深**/
	$(".nav-ul a").mouseover(function(){
		$(this).css("background-color","rgba(0,0,0,.5)");
	});
	$(".nav-ul a").mouseout(function(){
		$(this).css("background-color","#efefef");
	});

});