$(document).ready(function(){
		$("#flag").mouseover(function(){
			if($("#menu").is(':hidden')){   // �жϲ˵��Ƿ�Ϊ����״̬
				$("#menu").show(300);		// ������أ��򽫲˵���ʾ
			}
		});
		$("#menu").hover(null,function(){
			$("#menu").hide(300);		//���ز˵�
		});		
	});