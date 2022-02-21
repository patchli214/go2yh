function QueryString() {
    var name, value, i;
    var str = location.search;
    var num = str.indexOf("?");
    str = str.substr(num + 1);
    var arrtmp = str.split("&");
    for (i = 0; i < arrtmp.length; i++) {
        num = arrtmp[i].indexOf("=");
        if (num > 0) {
            name = arrtmp[i].substring(0, num);
            value = arrtmp[i].substr(num + 1);
            this[name] = value;
        }
    }
}

	function m_loadschool(){
		$("#c_title").html("全国"+school_sum+"所学校");
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

	function bottom_school(){
	$("#appointment_div").html('<form id="appointment" method="POST" action=""><div height="25" align="left" style="padding-left:5px;">孩子姓名:<input type="text" id="name2" name="name2"/></div><style>input[type="text"]{background-color:#FFF;width:180px;height:20px}</style><div height="25" align="left" style="padding-left:5px;padding-top:8px;">出生年月:<input type="date" id="year2" size="22" name="year2"/></div><div height="25" align="left" valign="middle" style="padding-left:5px;padding-top:8px;">性&nbsp;&nbsp;别： <input checked="" type="radio" id="male2" name="male" value="男"/>男 <input type="radio" id="male2" name="male" value="女"/>女 </div><style>input[type="date"]{width:180px;height:20px;background-color:#FFf}</style><div height="25" align="left" style="padding-left:5px;padding-top:8px;">联系电话:<input type="text" size="13" id="tel2" name="tel2"/></div><div height="25" align="left" style="padding-left:5px;padding-top:8px;">预约校区:<select class="city3" id="city2" style="width:186px;"></select></div><div width="180" border="0" cellpadding="0" cellspacing="0" style="vertical-align:middle;text-align:center;padding-top:8px;"><img id="submit_2" src="img/yuyue.png" onclick="check_input2();" style="cursor:pointer;"/></div></form>');
	var oCity2 = $('#city2');
	for(var i=0;i<cities_json["cities"][0]["schools"].length;i++){
		oCity2.append('<option>'+cities_json["cities"][0]["schools"][i]["school_name"]+'</option>');
	}
	}
	function m_loadall(cname){
		var cities = cities_json["cities"];
for(var j=0;j<cities.length;j++){
var city = cities_json["cities"][j];
var city_name = city["city_name"];
var schools = city["schools"];
		var colors = new Array();
		colors[0] = "f2b268"; //北京
		colors[1] = "b0e2d6"; //上海
		colors[2] = "eec0da"; //江浙
		colors[3] = "eaa6a7"; //重庆
		colors[4] = "c8caf0"; //天津
		colors[5] = "f3dea9"; //山东
		

		colors[6] = "f2b268"; //深圳
		colors[7] = "c1c48b"; //汕头
		colors[8] = "e8d7bb"; //河南
		colors[9] = "eaa6a7";
		
		var title_colors = new Array();
		title_colors[0] = "999999";
		title_colors[1] = "999999";
		title_colors[2] = "999999";
		title_colors[3] = "999999";
		title_colors[4] = "999999";
		title_colors[5] = "999999";
		title_colors[6] = "999999";
		title_colors[7] = "999999";
		title_colors[8] = "999999";
		title_colors[9] = "999999";
		title_colors[10] = "999999";
		title_colors[11] = "999999";
		title_colors[12] = "999999";

if ((cname=='1'&&city_name=='北京校区')||(cname=='2'&&city_name=='上海校区')||(cname=='3'&&city_name=='江浙校区')||(cname=='4'&&city_name=='重庆校区')||(cname=='5'&&city_name=='山东校区')||(cname=='6'&&city_name=='山东淄博校区')||(cname=='7'&&city_name=='山东东营校区')||(cname=='8'&&city_name=='山东青岛校区')||(cname=='6'&&city_name=='其他校区')){
        $("#all_school").append(' <div style="border-radius:8px;margin-top:0px;margin-left:12px;margin-right:12px;padding-top:10px;padding-bottom:10px;background:#ededed;text-align:center">    <span style="font-family:微软雅黑;font-size:17px;color:#'+title_colors[j]+';font-weight:bold;">&nbsp;'+city_name+'</span>	</div>');



		for(var i=0;i<schools.length;i++){
			thiscolor = colors[j]
			if(schools[i]["school_name"].indexOf("淄博")>-1)
				thiscolor = 'b0e2d6'
			if(schools[i]["school_name"].indexOf("东营")>-1)
				thiscolor = 'eec0da'
			if(schools[i]["school_name"].indexOf("青岛")>-1)
				thiscolor = 'eaa6a7'
			if (schools[i]["tel"]!='')
			    $("#all_school").append('<a href="tel:'+schools[i]["tel"]+'"><div style="border-radius:8px;margin-left:6px;margin-right:6px;margin-top:2px;padding-left:6px;padding-bottom:12px;padding-top:8px;background:#'+thiscolor+';"><span style="font-family:微软雅黑;font-size:11px;color:black;">&nbsp;'+schools[i]["school_name"]+'：'+schools[i]["school_add"]+'&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;'+schools[i]["tel"]+'</span></div></a>');
		    else
		        $("#all_school").append('<div style="border-radius:8px;margin-left:6px;margin-right:6px;margin-top:2px;padding-left:6px;padding-bottom:12px;padding-top:8px;background:#'+thiscolor+';"><span style="font-family:微软雅黑;font-size:11px;color:black;">&nbsp;'+schools[i]["school_name"]+'：'+schools[i]["school_add"]+' '+schools[i]["tel"]+'</span></div>');
		}
}
}
	}
	
	