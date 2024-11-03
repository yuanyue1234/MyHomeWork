 // 为li元素注册mouseover事件
	    $('.comment>li').mouseover(function(){
	        $(this).addClass('light').prevAll('li').addClass('light');
	        $(this).nextAll('li').removeClass('light');
	    });
	    // 为li元素注册mouseout事件
	    $('.comment>li').mouseout(function(){
	        $('.comment').find('li').removeClass('light')
	        $('.comment>li[light=on]').addClass('light').prevAll('li').addClass('light');
	    });
	    // 为li元素注册click事件
	    $('.comment>li').click(function(){
	        $(this).attr('light', 'on').siblings('li').removeAttr('light');
	    });