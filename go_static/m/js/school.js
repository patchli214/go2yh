var school_sum=223;
var cities_json = {
	"cities":[
		{"city_name":"北京校区","schools":[
				{"school_name":"中关村校区","school_add":"海淀区中关村东路66号世纪科贸大厦C1005(保福寺桥东南)","tel":"010-62670287"},
				{"school_name":"金源校区","school_add":"海淀区金源购物中心D段地下一层-1050号真朴围棋","tel":"010-53329267"},
				{"school_name":"五棵松校区","school_add":"海淀区永定路88号长银大厦（西点茂）B座","tel":"010-68107255"},
				{"school_name":"五棵松蓝港(卓展)","school_add":"海淀区复兴路69号卓展购物中心北楼3层(蓝色港湾)","tel":"010-88199529"},
				{"school_name":"公主坟校区","school_add":"海淀区西三环中路甲21号企业网大厦5层","tel":"010-63973060"},
				{"school_name":"崇文门校区","school_add":"东城区崇外大街新怡商务楼B座617(崇文门地铁站)","tel":"010-67084858"},
				{"school_name":"朝阳门校区","school_add":"东城区朝阳门 银河soho中心A座2层10223(朝阳门地铁站)","tel":"010-65206316"},
				{"school_name":"三里屯校区","school_add":"朝阳区三里屯SOHO5号商场3层5-356","tel":"010-57853495"},
				{"school_name":"富力广场","school_add":"北京市朝阳区东三环中路61号楼富力万丽酒店","tel":"010-59037277"},
				{"school_name":"远洋国际","school_add":"朝阳区八里庄西里61号楼远洋商务11层1102","tel":"010-65567451"},
				{"school_name":"蓝色港湾","school_add":"朝阳区朝阳公园路6号院蓝色港湾儿童城2层","tel":"010-59051775"},
				{"school_name":"奥运村校区","school_add":"朝阳区红军营南路安鑫办公2层(北辰购物中心斜对面)","tel":"010-84922240"},
				{"school_name":"华贸校区","school_add":"朝阳区清河营南街7号院3号楼地下一层-159(华贸天地)","tel":"010-59481176"},
				{"school_name":"望京校区","school_add":"朝阳区望京广顺北大街19号(六佰本商业街)南区二层A13a","tel":"010-61842197"},
				{"school_name":"悠乐汇校区","school_add":"朝阳区望京广顺南大街悠乐汇A6区2层221","tel":"010-84787566"},

				{"school_name":"国展天虹","school_add":"朝阳区左家庄北里58号天虹商场3层3097","tel":"010-56261193"},

				{"school_name":"上地校区","school_add":"海淀区科实大厦C座2层02A-2-3","tel":"010-82788370"},
				{"school_name":"阜成门校区","school_add":"西城区阜外大街2号万通新世界A座617","tel":"010-68394797"},
				{"school_name":"方庄校区","school_add":"丰台区方庄蒲黄榆地铁B口物美大卖场4层402","tel":"010-58070180"},

				{"school_name":"丰台槐房万达","school_add":"丰台区槐房万达广场2层2061(4号线新宫地铁站)","tel":"010-67916580"},
				{"school_name":"通州万达校区","school_add":"通州万达广场，万方家园底商","tel":"010-60539110"},

			]
		},
		{"city_name":"上海校区","schools":[
				{"school_name":"场中校区","school_add":"宝山区沪太路2388号文渊楼316室(7号场中路站)","tel":"021-60716265"},
				{"school_name":"联洋校区","school_add":"浦东新区长柳路58号证大立方大厦1楼102室（坐电梯从大堂G楼至1楼）","tel":"021-61555486"},
				{"school_name":"绿城校区","school_add":"浦东新区东绣路1426号真朴围棋2F(上海耀中国际学校斜对面)","tel":"021-50188826"},
				{"school_name":"源深校区","school_add":"浦东新区张杨路1657号二楼(6号线民生路站)","tel":"021-61312056"},
				{"school_name":"富都校区","school_add":"浦东新区东方路1367号富都广场2层11b(地铁4号线蓝村路站1号出口)","tel":"021-61107251"},
				{"school_name":"七宝校区","school_add":"闵行区七莘路3655号凯德七宝购物广场2层02／03号","tel":"021-61107252"},
				{"school_name":"鞍山校区","school_add":"杨浦区控江路2028号旭辉海上国际3楼301室","tel":"021-61312090"},

			]
		},
		{"city_name":"江浙校区","schools":[
				{"school_name":"南京万达广场","school_add":"南京市建邺区万达广场万达中心A座1409室","tel":"025-86750868"},
				{"school_name":"常州天宁","school_add":"常州九洲新世界商场2楼033号（北门巴黎贝甜楼上）","tel":"83605872"},
				{"school_name":"常州湖塘","school_add":"常州湖塘吾悦广场4楼407号（辛香汇对面）","tel":"81097581"},
				{"school_name":"常州宝龙","school_add":"常州钟楼区宝龙城市广场2楼C区（金宝贝旁）","tel":"85550576"},
				{"school_name":"无锡崇安","school_add":"无锡崇安区恒隆广场3楼340号","tel":"051082708521"},
				{"school_name":"苏州万科美好","school_add":"苏州市中新大道西229号万科美好广场","tel":"15151487095"},
                                                                {"school_name":"庆春银泰校区","school_add":"江干区景昙路18-26号银泰庆春店三楼","tel":"0571－86533632"},
				{"school_name":"杭州万宝城","school_add":"杭州市余杭区临平荷禹路105号万宝城A座509","tel":"0571-89358133"},
			]
		},
		{"city_name":"重庆校区","schools":[
				{"school_name":"财富中心","school_add":"渝北区洪湖东路1号财富购物中心LG层","tel":"023-88393899"},
				{"school_name":"西城天街","school_add":"九龙坡区杨家坪龙湖西城天街2层","tel":"023-81685789"},
                                                                {"school_name":"U城天街","school_add":"沙坪坝区大学城龙湖U城天街B馆3层 ","tel":"023-65068836"},
				{"school_name":"时代天街","school_add":"渝中区大坪龙湖时代天街C馆2层","tel":"023-81686068"},
				{"school_name":"上海城","school_add":"南岸区南坪百联上海城购物中心3层","tel":"023-62763700"},
			]
		},


		{"city_name":"山东校区","schools":[
						{"school_name":"济南历下","school_add":"济南市历下区七家村18号（中豪大酒店对面路南88米）","tel":"86981299"},
				{"school_name":"济南高新","school_add":"济南市高新区银座向北第三个楼崇华路中铁财智中心3号楼1107","tel":"88087979"},
				{"school_name":"济南市中","school_add":"济南市市中区八里洼路90号（伟东新都四区北门西侧）","tel":"88061416"},
				{"school_name":"济南历城","school_add":"济南市历城区七里河路与华龙路十字路口交汇处","tel":"88097979"},
				{"school_name":"济南槐荫","school_add":"济南市槐荫区和谐广场西100米（振兴花园3号楼1单元101室）","tel":"15725141411"},
				{"school_name":"济南天桥","school_add":"济南市天桥区工商河路13号翡翠郡南区5号楼1单元201室","tel":"88077979"},
				{"school_name":"济南名士豪庭","school_add":"济南市历下区经十路名士豪庭1号公建1301-1303室","tel":"18953122725"},
				{"school_name":"济南领秀城","school_add":"济南市市中区领秀城C区6号楼1单元202室","tel":"15065311012"},
				{"school_name":"济南燕山","school_add":"济南市历下区文化东路普利文东花园A座1单元1401","tel":"18854157500"},
				{"school_name":"济南龙奥","school_add":"历城区龙奥北路海信龙奥九号4号楼105室","tel":""},


				{"school_name":"淄博明清街","school_add":"淄博市张店区张桓路10号4层（明清街与联通路交叉口向南20米路东）","tel":"0533-3152333 "},
				{"school_name":"淄博世纪花园","school_add":"淄博市世纪花园小区内 幸福世家 老年大学","tel":""},
				{"school_name":"淄博人民东路","school_add":"淄博市张店区人民东路与东二路交叉口煤气大厦东临","tel":"15165847629"},
				{"school_name":"淄博恒基","school_add":"淄博市张店区商场西街与世纪路交叉路口","tel":"0533-2865000"},
				{"school_name":"淄博凯瑞","school_add":"淄博市张店区人民西路凯瑞景园综合楼三楼","tel":"15169367509"},
				{"school_name":"淄博亚运村","school_add":"淄博市张店区亚运村西门往北30米","tel":"13964471052"},
				{"school_name":"淄博银泰","school_add":"淄博市张店区银泰城3楼(喜悦滑冰场后)","tel":""},
				{"school_name":"淄博林泽","school_add":"淄博市张店区人民路与北京路路口北100米路东林泽花园对面50米","tel":"15753342801"},
				{"school_name":"淄博祥瑞园","school_add":"淄博市祥瑞园小学北门 宏程名座广场","tel":""},
				{"school_name":"淄博周村东校区","school_add":"淄博市青年路与正阳路路口东200米","tel":"0533-6170679"},
				{"school_name":"淄博周村西校区","school_add":"淄博市周村区新建中路与保安街交叉路口路北新北小区综合楼15号楼四楼","tel":"0533-6170679"},
				{"school_name":"淄博临淄中部","school_add":"淄博市临淄区太公路69号","tel":"15866288866"},
				{"school_name":"淄博临淄东部","school_add":"淄博市临淄天齐路与桓公路中国银行向南50米","tel":"13409054185"},
				{"school_name":"淄博临淄西部","school_add":"淄博市临淄区齐兴路172号福口居东临（虾吃虾涮二楼）","tel":"15866288866"},

				{"school_name":"东营西城校区","school_add":"东营市淄博路与云门山路交叉路口安泰阁三楼","tel":"0546—8717011"},
				{"school_name":"东营东城校区","school_add":"东营市郑州路与大渡河路交叉路口东南汇丰园商务楼三楼","tel":"0546—8026622"},
				{"school_name":"东营西城西三路","school_add":"东营市西三路科技一村东门对面三楼","tel":"0546—8771100"},
                                                                {"school_name":"东营东城东四路校区","school_add":"山东省东营市东四路与黄河路交叉口南188米路西","tel":""},
                                                                {"school_name":"东营利津校区","school_add":"山东省东营市利津县利一路118号（利华益小区对面）","tel":"0546-6366199"},

				{"school_name":"青岛新世界","school_add":"青岛市市南区福州南路9号新世界大厦1502室","tel":"0532-85762232"},
				{"school_name":"青岛金茂湾","school_add":"青岛市市南区四川路23号金茂湾购物中心L230商铺","tel":"0532-85762232"},
			]
		},
		{"city_name":"深圳校区","schools":[
				{"school_name":"前海花园","school_add":"前海花园32栋首层、前海花园三期会所二楼","tel":""},
				{"school_name":"阳光棕榈","school_add":"阳光文体中心2楼南山棋院内","tel":""},
				{"school_name":"鼎太校区","school_add":"鼎太风华六期商铺201","tel":""},
				{"school_name":"太子山庄校区","school_add":"太子山庄管理处三楼","tel":""},
				{"school_name":"南新校区","school_add":"南新路康德宠物医院二楼炫武艺学堂内（农行隔壁）","tel":""},
				{"school_name":"保利城校区","school_add":"保利城花园会所二楼","tel":""},
				{"school_name":"南山书城","school_add":"南山书城4楼","tel":""},
				{"school_name":"悠然校区","school_add":"悠然天地会所二楼","tel":""},
				{"school_name":"愉康校区","school_add":"深航飞行员公寓北座四楼会所内","tel":""},
				{"school_name":"麒麟校区","school_add":"麒麟花园金鳞阁美易艺术中心内","tel":""},
				{"school_name":"海文校区","school_add":"海文花园会所二楼","tel":""},
				{"school_name":"星海名城","school_add":"星海名城一期四组团10栋1D","tel":""},
				{"school_name":"科技园北区","school_add":"科苑学里3栋1楼","tel":""},
				{"school_name":"松坪校区","school_add":"松坪村社区服务中心内","tel":""},
				{"school_name":"桂苑校区","school_add":"沙河东路桂苑小区1栋1楼","tel":""},
				{"school_name":"锦绣花园","school_add":"锦绣花园会所二楼","tel":""},
				{"school_name":"生态广场","school_add":"生态广场乐林琴行内","tel":""},
				{"school_name":"桃源校区","school_add":"桃源村94栋2楼","tel":""},
				{"school_name":"罗湖校区","school_add":"罗湖深圳书城（金山大厦1902）","tel":""},
				{"school_name":"浪琴屿校区","school_add":"浪琴屿会所一楼","tel":""},
				{"school_name":"漾日湾部","school_add":"海德四道漾日湾畔四栋12B","tel":""},
				{"school_name":"蛇口学区","school_add":"蛇口青少年活动中心四楼","tel":""},
				{"school_name":"海月校区","school_add":"海月一期、二期、三期会所内","tel":""},
				{"school_name":"桃花源校区","school_add":"名兰苑酒店三楼","tel":""},
				{"school_name":"BABY校区","school_add":"蛇口中心路南端鸿威海怡湾商场二楼","tel":""},
				{"school_name":"雍景湾校区","school_add":"雍景湾会所二楼","tel":""},
				{"school_name":"科技园南区","school_add":"阳光带海滨城二期、一期会所内","tel":""},
				{"school_name":"橡皮树校区","school_add":"华侨城侨城1街橡皮树创意坊D2栋1楼（首地容御附近）","tel":""},
				{"school_name":"留仙校区","school_add":"西丽天虹后面学城艺术中心二楼","tel":""},
				{"school_name":"平山校区","school_add":"西丽平山一路民企科技园8栋310（平山小学附近）","tel":""},
				{"school_name":"华丽校区","school_add":"罗湖华丽路环岛丽园会所三楼","tel":""},
				{"school_name":"布吉校区","school_add":"布吉信义荔山公馆8号楼小牡丹艺术中心内","tel":""},
			]
		},
		{"city_name":"汕头校区","schools":[
				{"school_name":"长平校区","school_add":"长平路55号长平大厦四楼","tel":""},
				{"school_name":"金泰校区","school_add":"金泰庄62栋（星湖公园旁）","tel":""},
				{"school_name":"书城校区","school_add":"汕头市购书中心四楼","tel":""},
				{"school_name":"广夏校区","school_add":"翠云园1栋13号铺面一至二楼","tel":""},
				{"school_name":"博爱校区","school_add":"博爱路10号市体育局社体中心5楼","tel":""},
				{"school_name":"潮南校区","school_add":"潮南区峡山金祥路","tel":""},
				{"school_name":"鮀浦校区","school_add":"金环西路乐业园B区对面慧德幼儿园","tel":""},
				{"school_name":"普宁校区","school_add":"普宁流沙培英园北区22栋","tel":""},
				{"school_name":"揭阳东山","school_add":"揭阳市东山八号街市实验中学西侧","tel":""},
				{"school_name":"揭阳榕城","school_add":"揭阳市榕城江南新城一期会所东侧","tel":""},
			]
		},
		{"city_name":"其他校区","schools":[
				{"school_name":"宝龙校区","school_add":"郑州市郑东新区农业东路九如路宝龙城市广场b区3212","tel":"0373-56289297"},
			]
		},

	]
};
