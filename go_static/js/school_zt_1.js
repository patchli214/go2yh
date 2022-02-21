

	function m_loadschool(){
		$("#c_title").html("全国"+school_sum+"个教室");
		$("#c_title2").html("北京"+cities_json["cities"][0]["schools"].length+"所校区&nbsp;&nbsp;&nbsp;&nbsp;家门口的围棋学校");
		var schools = cities_json["cities"][0]["schools"];
		var colors = new Array();
		colors[0] = "f66a69";
		colors[1] = "ff9600";
		colors[2] = "2ba0a7";
		colors[3] = "9b66ae";

		for(var i=0;i<schools.length;i++){
			var color = colors[i%4];
			var space = '';
			if(i%4==3||i==schools.length-1)space = 'padding-bottom:10px;';
			$("#c2div").append('<div style="'+space+'position:relative;left:0px;top:-60px;background:#3a3a38;"><div style="border-radius:6px;margin-left:6px;margin-right:6px;padding-bottom:4px;background:#'+color+';"><span style="font-family:微软雅黑;font-size:13px;color:white;margin-left:6px;"></span><span style="font-family:微软雅黑;font-size:11px;color:white;">'+schools[i]["school_name"]+'：'+schools[i]["school_add"]+'    </span>	</div>  </div>');
		}
	}

	function bottom_school(tel){
		console.log(tel)
	$("#appointment_div").html('<form id="appointment" method="POST" action=""><div style="color:red;font-size:24px;">请拨打'+tel+'索取</div><div style="color:black;font-size:24px;">免费试听名额</div><div height="25" align="left" style="padding-left:5px;">孩子姓名:<input type="text" id="name2" name="name2"/></div><style>input[type="text"]{background-color:#FFF;width:180px;height:20px}</style><div height="25" align="left" valign="middle" style="padding-left:5px;padding-top:8px;">性&nbsp;&nbsp;别： <input checked="" type="radio" id="male2" name="male" value="男"/>男 <input type="radio" id="male2" name="male" value="女"/>女 </div><style>input[type="date"]{width:180px;height:20px;background-color:#FFf}</style><div height="25" align="left" style="padding-left:5px;padding-top:8px;">联系电话:<input type="text" size="13" id="tel2" name="tel2"/></div><div height="25" align="left" style="padding-left:5px;padding-top:8px;">预约校区:<select class="city3" id="city2" style="width:186px;"></select></div><div width="180" border="0" cellpadding="0" cellspacing="0" style="vertical-align:middle;text-align:center;padding-top:8px;"><img id="submit_2" src="img/yuyue.png" onclick="check_input2();" style="cursor:pointer;"/></div></form>');
	var oCity2 = $('#city2');
	for(var i=0;i<cities_json["cities"][0]["schools"].length;i++){
		oCity2.append('<option>'+cities_json["cities"][0]["schools"][i]["school_name"]+'</option>');
	}
	}
	function m_loadall(){
		var cities = cities_json["cities"];
for(var j=0;j<cities.length;j++){
var city = cities_json["cities"][j];
var city_name = city["city_name"];
var schools = city["schools"];
		var colors = new Array();
		colors[0] = "f2b268";
		colors[1] = "c1c48b";
		colors[2] = "eaa6a7";
		colors[3] = "f3dea9";
		colors[4] = "eec0da";
		colors[5] = "b0e2d6";
		colors[6] = "c8caf0";
		colors[7] = "e8d7bb";
		colors[8] = "f2b268";
		colors[9] = "c1c48b";
		colors[10] = "eaa6a7";
		var title_colors = new Array();
		title_colors[0] = "fa8601";
		title_colors[1] = "909807";
		title_colors[2] = "c85355";
		title_colors[3] = "d69e12";
		title_colors[4] = "e23e95";
		title_colors[5] = "2fb695";
		title_colors[6] = "6a71c9";
		title_colors[7] = "78520b";
		title_colors[8] = "fa8601";
		title_colors[9] = "909807";
		title_colors[10] = "c85355";


$("#all_school").append(' <div style="border-radius:8px;margin-top:6px;margin-left:12px;margin-right:12px;padding-bottom:4px;background:#ededed;">    <span style="font-family:微软雅黑;font-size:17px;color:#'+title_colors[j]+';font-weight:bold;">&nbsp;'+city_name+'</span>	</div>');



		for(var i=0;i<schools.length;i++){
			$("#all_school").append('<div style="border-radius:8px;margin-left:6px;margin-right:6px;margin-top:2px;padding-left:6px;padding-bottom:4px;background:#'+colors[j]+';"><span style="font-family:微软雅黑;font-size:11px;color:black;">&nbsp;'+schools[i]["school_name"]+'：'+schools[i]["school_add"]+'</span></div>');
		}
}
	}
