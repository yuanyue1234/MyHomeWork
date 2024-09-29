  $(function() {
			//对标题超链接 你是人间四月天设置样式
	        $("#a").css({"color": "red", "text-decoration": "none"});
	      
	       //对查安全部超链接设置隐藏/显示的切换效果
	        $("#c").click(function () {
	            $(".five").toggle();
	        });
			//对内容简介 设置样式
			$(".three").css({"border": "1px solid white", 
			                 "height": "34px",
							 "width": "1534px",
							 "color": "white",
							 "background-color":"gray",
							 "font-weight": "bold",
							 "padding": "11px 0px 0px 24px"
							});
				      
			//对标题设置单击事件
	        $("#a").click(function () {
	            $(this).css({"color": "blue", "font-size": "30px"});
	            $("#b").next().css("color", "green");	
	        });
	    });
		
		
		
		