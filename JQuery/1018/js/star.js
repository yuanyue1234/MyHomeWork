 // ΪliԪ��ע��mouseover�¼�
	    $('.comment>li').mouseover(function(){
	        $(this).addClass('light').prevAll('li').addClass('light');
	        $(this).nextAll('li').removeClass('light');
	    });
	    // ΪliԪ��ע��mouseout�¼�
	    $('.comment>li').mouseout(function(){
	        $('.comment').find('li').removeClass('light')
	        $('.comment>li[light=on]').addClass('light').prevAll('li').addClass('light');
	    });
	    // ΪliԪ��ע��click�¼�
	    $('.comment>li').click(function(){
	        $(this).attr('light', 'on').siblings('li').removeAttr('light');
	    });