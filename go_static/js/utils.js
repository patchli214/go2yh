/**
 * Created by bee on 2016/10/19.
 */
/**
 * Created by bee on 15/12/16.
 */
$(document).ready(function() {
  var href = window.location.href
  console.log(href)
  if(href.indexOf("127.0.0.1")>-1){
    console.log('LOCAL')
    $("title").html("LOCAL真朴CRM")
  }
  if(href.indexOf("test")>-1){
    console.log('TEST')
    $("title").html("TEST真朴CRM")
  }

})

function isMobileNum(s)
{
var patrn=/^[0-9-() +]{11}$/;
if (!patrn.exec(s)) return false
return true
}

function checkInput(){
    var tel = $("#prt1mobile").val()
    if(!isMobileNum(tel)){
        alert('手机号码错误，请重新填写。')
        return
    }else{
        document.getElementById("form1").submit()
    }
}


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

function getRequestUrl(path, key, value) {
    var url = "";
    var str = location.search;
    var Request = new QueryString();
    var num = str.indexOf("?");
    str = str.substr(num + 1);
    var arrtmp = str.split("&");
    var a = Request[key];
    if (a) {
        for (i = 0; i < arrtmp.length; i++) {
            num = arrtmp[i].indexOf(key);
            if (num > -1) {
                arrtmp.splice(i, 1);
                break;
            }
        }
    }
    arrtmp.push(key + "=" + value);
    url = arrtmp.join("&");
    url = path + "?" + url;
    console.log(url);
    return url
}


function isEmpty(obj) {
    for (var name in obj) {
        return false;
    }
    return true;
}

function mobileCheck() {
	  var check = false;
	  (function(a){if(/(android|bb\d+|meego).+mobile|avantgo|bada\/|blackberry|blazer|compal|elaine|fennec|hiptop|iemobile|ip(hone|od)|iris|kindle|lge |maemo|midp|mmp|mobile.+firefox|netfront|opera m(ob|in)i|palm( os)?|phone|p(ixi|re)\/|plucker|pocket|psp|series(4|6)0|symbian|treo|up\.(browser|link)|vodafone|wap|windows ce|xda|xiino/i.test(a)||/1207|6310|6590|3gso|4thp|50[1-6]i|770s|802s|a wa|abac|ac(er|oo|s\-)|ai(ko|rn)|al(av|ca|co)|amoi|an(ex|ny|yw)|aptu|ar(ch|go)|as(te|us)|attw|au(di|\-m|r |s )|avan|be(ck|ll|nq)|bi(lb|rd)|bl(ac|az)|br(e|v)w|bumb|bw\-(n|u)|c55\/|capi|ccwa|cdm\-|cell|chtm|cldc|cmd\-|co(mp|nd)|craw|da(it|ll|ng)|dbte|dc\-s|devi|dica|dmob|do(c|p)o|ds(12|\-d)|el(49|ai)|em(l2|ul)|er(ic|k0)|esl8|ez([4-7]0|os|wa|ze)|fetc|fly(\-|_)|g1 u|g560|gene|gf\-5|g\-mo|go(\.w|od)|gr(ad|un)|haie|hcit|hd\-(m|p|t)|hei\-|hi(pt|ta)|hp( i|ip)|hs\-c|ht(c(\-| |_|a|g|p|s|t)|tp)|hu(aw|tc)|i\-(20|go|ma)|i230|iac( |\-|\/)|ibro|idea|ig01|ikom|im1k|inno|ipaq|iris|ja(t|v)a|jbro|jemu|jigs|kddi|keji|kgt( |\/)|klon|kpt |kwc\-|kyo(c|k)|le(no|xi)|lg( g|\/(k|l|u)|50|54|\-[a-w])|libw|lynx|m1\-w|m3ga|m50\/|ma(te|ui|xo)|mc(01|21|ca)|m\-cr|me(rc|ri)|mi(o8|oa|ts)|mmef|mo(01|02|bi|de|do|t(\-| |o|v)|zz)|mt(50|p1|v )|mwbp|mywa|n10[0-2]|n20[2-3]|n30(0|2)|n50(0|2|5)|n7(0(0|1)|10)|ne((c|m)\-|on|tf|wf|wg|wt)|nok(6|i)|nzph|o2im|op(ti|wv)|oran|owg1|p800|pan(a|d|t)|pdxg|pg(13|\-([1-8]|c))|phil|pire|pl(ay|uc)|pn\-2|po(ck|rt|se)|prox|psio|pt\-g|qa\-a|qc(07|12|21|32|60|\-[2-7]|i\-)|qtek|r380|r600|raks|rim9|ro(ve|zo)|s55\/|sa(ge|ma|mm|ms|ny|va)|sc(01|h\-|oo|p\-)|sdk\/|se(c(\-|0|1)|47|mc|nd|ri)|sgh\-|shar|sie(\-|m)|sk\-0|sl(45|id)|sm(al|ar|b3|it|t5)|so(ft|ny)|sp(01|h\-|v\-|v )|sy(01|mb)|t2(18|50)|t6(00|10|18)|ta(gt|lk)|tcl\-|tdg\-|tel(i|m)|tim\-|t\-mo|to(pl|sh)|ts(70|m\-|m3|m5)|tx\-9|up(\.b|g1|si)|utst|v400|v750|veri|vi(rg|te)|vk(40|5[0-3]|\-v)|vm40|voda|vulc|vx(52|53|60|61|70|80|81|83|85|98)|w3c(\-| )|webc|whit|wi(g |nc|nw)|wmlb|wonu|x700|yas\-|your|zeto|zte\-/i.test(a.substr(0,4))) check = true;})(navigator.userAgent||navigator.vendor||window.opera);
	  return check;
}

function isWeiXin(){
    var ua = window.navigator.userAgent.toLowerCase();
    if(ua.match(/MicroMessenger/i) == 'micromessenger'){
        return true;
    }else{
        return false;
    }
}

function getCookie(c_name) {
    if (document.cookie.length > 0) {
        c_start = document.cookie.indexOf(c_name + "=");
        if (c_start != -1) {
            c_start = c_start + c_name.length + 1;
            c_end = document.cookie.indexOf(";", c_start);
            if (c_end == -1) c_end = document.cookie.length;
            return document.cookie.substring(c_start, c_end);
        }
    }
    return ""
}

function inform(first,openId,keyword2,keyword3,keyword4,keyword5){
	var keyword1 = "真朴围棋";
		console.log(openId);
	console.log(first);
	console.log(keyword1);
	console.log(keyword2);
	console.log(keyword3);
	console.log(keyword4);
	console.log(keyword5);
    $.post("https://rang.jieli360.com/web/sendWX",
		  {
			first:first,
    	openId:openId,
			keyword1:keyword1,
			keyword2:keyword2,
			keyword3:keyword3,
			keyword4:keyword4,
			keyword5:keyword5,
			url:'http://www.go2crm.cn'
		  },
		  function(data,status){

		      console.log('finish');
		  });

}

Date.prototype.Format = function (fmt) { //author: meizz
	//var fmt = "yyyy-MM-dd hh:mm:ss";
	//var date = new Date();
	//var datestring = date.Format(fmt);
    var o = {
        "M+": this.getMonth() + 1, //月份
        "d+": this.getDate(), //日
        "h+": this.getHours(), //小时
        "m+": this.getMinutes(), //分
        "s+": this.getSeconds(), //秒
        "q+": Math.floor((this.getMonth() + 3) / 3), //季度
        "S": this.getMilliseconds() //毫秒
    };
    if (/(y+)/.test(fmt)) fmt = fmt.replace(RegExp.$1, (this.getFullYear() + "").substr(4 - RegExp.$1.length));
    for (var k in o)
    if (new RegExp("(" + k + ")").test(fmt)) fmt = fmt.replace(RegExp.$1, (RegExp.$1.length == 1) ? (o[k]) : (("00" + o[k]).substr(("" + o[k]).length)));
    return fmt;
}

function numToCny(money) {
　　var cnNums = new Array("零", "壹", "贰", "叁", "肆", "伍", "陆", "柒", "捌", "玖"); //汉字的数字
　　var cnIntRadice = new Array("", "拾", "佰", "仟"); //基本单位
　　var cnIntUnits = new Array("", "万", "亿", "兆"); //对应整数部分扩展单位
　　var cnDecUnits = new Array("角", "分", "毫", "厘"); //对应小数部分单位
　　var cnInteger = "整"; //整数金额时后面跟的字符
　　var cnIntLast = "元"; //整型完以后的单位
　　var maxNum = 999999999999999.9999; //最大处理的数字
　　var IntegerNum; //金额整数部分
　　var DecimalNum; //金额小数部分
　　var ChineseStr = ""; //输出的中文金额字符串
　　var parts; //分离金额后用的数组，预定义
　　if (money == "") {
　　return "";
　　}
　　money = parseFloat(money);
　　if (money >= maxNum) {
　　alert('超出最大处理数字');
　　return "";
　　}
　　if (money == 0) {
　　ChineseStr = cnNums[0] + cnIntLast + cnInteger;
　　return ChineseStr;
　　}
　　money = money.toString(); //转换为字符串
　　if (money.indexOf(".") == -1) {
　　IntegerNum = money;
　　DecimalNum = '';
　　} else {
　　parts = money.split(".");
　　IntegerNum = parts[0];
　　DecimalNum = parts[1].substr(0, 4);
　　}
　　if (parseInt(IntegerNum, 10) > 0) { //获取整型部分转换
　　var zeroCount = 0;
　　var IntLen = IntegerNum.length;

　　for (var i = 0; i < IntLen; i++) {
　　var n = IntegerNum.substr(i, 1);
　　var p = IntLen - i - 1;
　　var q = p / 4;
　　var m = p % 4;

　　if (n == "0") {
　　zeroCount++;
　　} else {
　　if (zeroCount > 0) {
　　ChineseStr += cnNums[0];
　　}

　　zeroCount = 0; //归零

　　ChineseStr += cnNums[parseInt(n)] + cnIntRadice[m];
　　}
　　if (m == 0 && zeroCount < 4) {
　　ChineseStr += cnIntUnits[q];
　　}
　　}
　　ChineseStr += cnIntLast;
　　//整型部分处理完毕
　　}
　　if (DecimalNum != '') { //小数部分
　　var decLen = DecimalNum.length;
　　for (var i = 0; i < decLen; i++) {
　　var n = DecimalNum.substr(i, 1);
　　if (n != '0') {
　　ChineseStr += cnNums[Number(n)] + cnDecUnits[i];
　　}
　　}
　　}
　　if (ChineseStr == '') {
　　ChineseStr += cnNums[0] + cnIntLast + cnInteger;
　　} else if (DecimalNum == '') {
　　ChineseStr += cnInteger;
　　}
　　return ChineseStr;
　　}


var _hmt = _hmt || [];
(function() {
  var hm = document.createElement("script");
  hm.src = "https://hm.baidu.com/hm.js?1416fccdedb781f5c615ac16f6946ced";
  var s = document.getElementsByTagName("script")[0];
  s.parentNode.insertBefore(hm, s);
})();
