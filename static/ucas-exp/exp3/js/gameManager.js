function GameManager(mode){
	_this  = this
	this.ajax = new modAjax()
	this.routeTableScale = 5
	this.info = null
	this.group_users=null
	this.mode = mode
	if(mode == "formal"){
		this.ajax.mode = 0
	}
	// 以下字段都要进行刷新
	this.nodes = null // 小组成员对应拥有的结点序号
	this.topo = null
	
}

GameManager.prototype.errorHandler = function() {
	alert("游戏前请先登录");
};

GameManager.prototype.getinfo = function(){
	this.ajax.getinfo(function(data){
		$("#login_info").text(data['info']["name"])
		_this.info = data['info']
		_this.group_users = data['group_users']
		if(_this.checkStatus(data)==false)return
		var times = data['gameTimes']
		var step = data['step']
		group_users = data['group_users']
		group_name = data['info']['group']
		$("#group-head").text(group_name+"  Group Members")
		info_html = '<ul>'
		for(var i = 0; i<group_users.length; i++) {
			info_html += '<li id="'+group_users[i]['userId']+'">'+group_users[i]['name']+'</li>'
		}
		info_html += '</ul>'
		var info_dom= $(info_html).listview();
		info_dom.insertAfter($('#group-head'))
		$("li#"+_this.info['userId']).css("color", "red")

		_this.ajax.times = times

		// 添加基础按钮
		$('<div id="actionButtonDiv"><input id="actionButton" type="button" value="Choose Network Topology" /></div>').insertAfter("#actionLable")
		if(_this.mode=="test"){
			$("<div id='clearRecordDiv'><input id='clearRecord' type='button' value='Clear and Restart'/></div>").insertAfter("#gameMode")
			$("#clearRecord").button({icon:"delete"})
			$("#clearRecord").on("click", function(){
				if(confirm("测试模式下可清除全组的测试数据，实验从头开始。清除后不可恢复，确认清除？") == true){
					_this.ajax.clearRouteRecordInTestMode(function(data){
						if(data["status"] == "NORMAL"){
							alert("测试模式数据已清除，小组可重新开始")
							location.reload()
							return
						}else {
							alert("正式实验下无法清除数据")
							location.reload()
							return
						}
					}, _this.errorHandler)
				}
			});
		}

		if(step == 0){
			$("#statusText").text("You should choose a network topoloy, click to choose")
			$("#actionButton").val("Choose Network Topology")
			$("#actionButton").button({icon:"tag"})
			$("#actionButton").button("refresh")
			$("#actionButton").off("click")
			$("#actionButton").on("click", function(){
				_this.firstStep()
			});
		} else if(step == 1) {
			$("#statusText").text("Network topology has been decided, click to design")
			$("#actionButton").val("Design Routing Table")
			$("#actionButton").button({icon:"tag"})
			$("#actionButton").button("refresh")
			$("#actionButton").off("click")
			$("#actionButton").on("click", function(){
				_this.secondStep()
			});
		}
		else if(step == 3){
			$("#statusText").text("The experiment is end!")
			var str = "客户端获得平均速率:  " + (data["averageRateScore"]).toFixed(2) + "Mbps </br>客户端到服务器平均路径长度为"+(data["averageLengthScore"]).toFixed(2)+" </br>实验测评是:  "+  data["finalScore"] +"</br>实验结束后，会根据所有同学实验情况进行给分。"
			$("<div><h3>实验测评</h3><span class='middle-text' style='color:red;font-size:1em'>"+str+"</span></div>").appendTo("#ControlBoard")
			$("#gameAction").remove()
		}

	},this.errorHandler)
};

// 得到随机的拓扑图
GameManager.prototype.firstStep = function() {
	_this.ajax.topoScale = 30
	_this.ajax.getTopo(_this.firstStepCallback, _this.errorHandler)
}

GameManager.prototype.initTopoMatrix = function(data) {
	// 移除canvas元素和popup的DOM
	paper.project.activeLayer.removeChildren()
	$('table[id^=route-table]').remove()

	_this.topo = new Topology(data['scale'], 0, 0)
	var link = data['link']
	for(var i = 0; i < link.length; i++) {
		var tmp = link[i].split("-")
		_this.topo.matrix.link(tmp[0], tmp[1])
	}
	paintTopo(data["status"], _this.topo, _this.info, _this.nodes, _this.myRoute, _this.routeTableScale);
	paper.project.activeLayer.view.update()
}

GameManager.prototype.setDistributedNodesAndRoute = function(data) {
	_this.nodes = data['distributeNodes']
	_this.myRoute = {}
	for(var i = 0; i<_this.group_users.length; i++) {
		var tmpUserId = group_users[i]['userId']
		$("li#"+tmpUserId).text(group_users[i]['name']+'(' + _this.nodes[tmpUserId].toString() + ')')
	}
	for(var index in _this.nodes[_this.info['userId']]){
		var myNode = _this.nodes[_this.info['userId']][index]
		if(myNode.toString() in data['route'])
			_this.myRoute[myNode.toString()] = data['route'][myNode.toString()]
	}
}

GameManager.prototype.firstStepCallback = function(data) {
	if(data['status'] == "NA"){
		alert("您不在此实验可做日期之间，无法开始")
		return false
	}
	// 针对的是getTopo中的topo的status为CHOOSING
	if(data['status'] != -1){
		alert("某组员已经选择了网络拓扑图，无法再选择，网页将会刷新。")
		location.reload()
		return false
	}
	_this.initTopoMatrix(data)
	$("#statusText").text("Step 1: Choose a network topopoly(Your team can't choose anymore when any member of your group decided a network topology)")
	$("<div id='nextTopoDiv'><input id='nextTopo' type='button' value='Change'/></div>").insertBefore("#actionButtonDiv")
	$("#nextTopo").button({icon:"refresh"})
	$("#nextTopo").on("click", function(){
		$("#nextTopoDiv").remove()
		_this.firstStep();
	});
	$("#actionButton").val("Choose This")
	$("#actionButton").button({icon:"lock"})
	$("#actionButton").button("refresh")
	$("#actionButton").off("click")
	$("#actionButton").on("click", function(){
		$("#nextTopoDiv").remove();
		data["status"] = 0 // 将status改成TopoStatus["NEW"]
		_this.ajax.data = JSON.stringify(data)
		_this.ajax.submitTopo(function(data){
			// console.log(data)
			if(data["status"] == "NORMAL")
				_this.secondStep()
			// to test
			else if(data["status"] == "someoneSubmited"){
				alertStr = "提交出错，小组某成员已经确认了网络拓扑图。";
				alert(alertStr);
				location.reload()
			}
			else
				_this.firstStep()
		}, _this.errorHandler)
	});
}

// 从服务器得到选定的拓扑图和每人的路由，并做一些渲染
GameManager.prototype.secondStep = function() {
	this.ajax.getTopo(_this.secondStepCallback, _this.errorHandler)
}

GameManager.prototype.secondStepCallback = function(data) {
	if(_this.checkStatus(data)==false)return
	_this.setDistributedNodesAndRoute(data)
	_this.initTopoMatrix(data)
	$("#statusText").text("Step 2: Design Routing Table")
	$("<div id='evaluateRouteDiv'><input id='evaluateRoute' type='button' value='Test and Simulate'/></div>").insertAfter("#actionButtonDiv")
	$("#evaluateRoute").button({icon:"eye"})
	$("#evaluateRoute").on("click", function(){
		if(confirm("此按钮不会保存当前节点的路由，请组员注意保存，模拟路由会模拟当前所有组员保存最新路由表。确认继续模拟？") == true){_this.thirdStep();$("#evaluateRouteDiv").remove()}
	});
	$("#actionButton").val("Save the Design")
	$("#actionButton").button({icon:"check"})
	$("#actionButton").button("refresh")
	$("#actionButton").off("click")
	$("#actionButton").on("click", function(){
		
		var _result = {}
		var my_nodes = _this.nodes[_this.info['userId']]
		for(var j in my_nodes){
			var table = []
			for(var i =1; i <= _this.routeTableScale; i++) {
				var dest = $("#dest-" + my_nodes[j] + i).val();
				var next = $("#next-" + my_nodes[j] + i).val();
				if(dest==null || dest=="")dest = "null";
				if(next==null || next=="")next = "null";
				var flag = checkRouteRecord(dest, next, _this.topo.avaliableLength)
				if( flag == -1){
					alert("节点"+my_nodes[j]+"的路由输入不满足格式（英文半角逗号分隔），请重新修改")
					return
				} else if(flag == -2){
					alert("节点"+my_nodes[j]+"的路由输入的数字不在节点范围内，请重新修改")
					return
				} else if(flag == -3){
					alert("节点"+my_nodes[j]+"的路由输入的逗号多余，请重新修改")
					return
				}
				var tmp ={}
				tmp[dest] = next
				table.push(tmp)
			}
			_result[my_nodes[j]] = table
		}
		// console.log(JSON.stringify(_result))
		$("#evaluateRouteDiv").remove()
		_this.ajax.result = JSON.stringify(_result)
		_this.ajax.submitRoute(_this.submitRouteCallback, _this.errorHandler)
	});
}

GameManager.prototype.submitRouteCallback = function(data) {
	if(_this.checkStatus(data)==false)return
	var status = data["status"]
	var alertStr = null
	// console.log(status)
	if(status == "ERROR"){
		alertStr = "提交出错，可能原因是没有获取拓扑图。将刷新页面。";
		alert(alertStr);
		location.reload() 
		return
	} else if(status == "REJECT") {
		alertStr = "实验结果已经提交，无法修改";
		alert(alertStr);
		location.reload() 
		return
	} else {
		alert("保存路由成功");
		_this.secondStep()
	}
}

// 模拟路由，进入模拟路由后，每次点击“再次模拟”都会再请求服务器数据。这个需要和同学说明
GameManager.prototype.thirdStep = function() {
	_this.ajax.getTopo(_this.thirdStepCallback, _this.errorHandler)
}

GameManager.prototype.thirdStepCallback = function(data) {
	if(_this.checkStatus(data)==false)return
	if(_this.initRouteEvaluation(data, true) == -1) return

	$("#statusText").text("Step3: Simulate the whole network.")
	$("<div id ='returnRouteDiv'><input id='returnRoute' type='button'  value='Return to Modify'/><div>").insertBefore("#actionButtonDiv")
	$("#returnRoute").button({ icon: "edit" })
	$("#returnRoute").on("click", function(){
		$("#evaluateRouteAgainDiv").remove();$("#returnRouteDiv").remove();$("#saveImageDiv").remove();_this.secondStep();
	});
	$("<div id='saveImageDiv'><input id='saveImage' type='button'  value='Download Image'/></div>").insertBefore("#actionButtonDiv")
	$("#saveImage").button({ icon: "action" })
	$("#saveImage").on("click", function(){
		var dataURL = document.getElementById("canvas").toDataURL('image/png');
		window.open(dataURL, "_blank");
	});
	$("<div id='evaluateRouteAgainDiv'><input id='evaluateRouteAgain' type='button' value='Simulate Again'/></div>").insertBefore("#actionButtonDiv")
	$("#evaluateRouteAgain").button({icon:"refresh"})
	$("#evaluateRouteAgain").on("click", function(){
		if(confirm("模拟路由会模拟当前所有组员保存最新路由表，请组员注意保存当前工作。确认模拟？")){$("#evaluateRouteAgainDiv").remove();$("#returnRouteDiv").remove();$("#saveImageDiv").remove();_this.thirdStep()}
	});
	

	$("#actionButton").val("Submit Experiment")
	$("#actionButton").button({ icon: "lock" })
	$("#actionButton").button("refresh")
	$("#actionButton").off("click")
	$("#actionButton").on("click", function(){
		if(confirm("提交前会请求全组最新的路由进行测试，确认测试？") == true){
			// 请求服务器最新数据
			_this.ajax.getTopo(function(data){
				if(_this.checkStatus(data)==false)return
				_this.topo = new Topology(data['scale'], 0, 0)
				var link = data['link']
				for(var i = 0; i < link.length; i++) {
					var tmp = link[i].split("-")
					_this.topo.matrix.link(tmp[0], tmp[1])
				}
				var error = []
				if(runRoute(_this.topo, data["route"], error) == false){
					alert("路由表设计有误，" + error[0] +"--" + error[1] + "不通，请设计者修改")
					$("#returnRouteDiv").remove();
					$("#saveImageDiv").remove();
					$("#evaluateRouteAgainDiv").remove();
					_this.secondStep();
					return
				}else{
					if(confirm("测试无误。提交后全组实验结束，确认提交答案？") == true){
						$("#returnRouteDiv").remove();
						$("#saveImageDiv").remove();
						$("#evaluateRouteAgainDiv").remove();
						_this.fourthStep(data)
					}
				}

			}, _this.errorHandler)
		}
	});
}

// 提交结果，随机模拟5次；取每次模拟中，每个客户端得到的带宽，去掉最低和最高带宽，得到平均值；然后对5次再取一个平均值
GameManager.prototype.fourthStep = function(data) {
	if(data['status'] == "NA"){
		alert("您不在此实验可做日期之间，无法开始")
		return
	}
	var times = 40
	var rateSum = 0, lengthSum = 0
	var practiceRateScore =[], practiceLengthScore=[]
	for(var i = 0;i<times;i++){
		var tmpResult = _this.initRouteEvaluation(data,false)
		if(tmpResult == -1)return
		// console.log("times-" + i + ": 	" + tmpResult)
		rateSum += tmpResult[0]
		lengthSum += tmpResult[1]
		practiceRateScore.push(tmpResult[0])
		practiceLengthScore.push(tmpResult[1])
	}
	var rateResult = rateSum / times
	var lengthResult = lengthSum / times
	// result在18~63范围
	var finalScore = parseInt((rateResult-18)/(63-18)*20 + 65 + (15 - (lengthResult-3)/(10-3)*15))
	if(finalScore > 100)finalScore=100
	// console.log("客户端获得平均速率:  " + (rateResult).toFixed(2) + "Mbps </br>客户端到服务器平均路径长度为"+(lengthResult).toFixed(2)+" </br>实验测评得分是"+ finalScore)
	_this.ajax.score = JSON.stringify({"averageRateScore":rateResult,"averageLengthScore":lengthResult, "practiceRateScore":practiceRateScore, "practiceLengthScore":practiceLengthScore, "finalScore":finalScore})
	_this.ajax.submitRouteEvaluation(function(data){
		// console.log(data)
		if(data["status"]=="DONE"){
			alert("其他组员已提交成绩，实验已结束。")
			location.reload()
			return
		} else if(data["status"]=="ERROR"){
			alert("提交出错")
			location.reload()
			return
		}else{
			// console.log(data)
			alert("客户端获得平均速率:  " + (data["averageRateScore"]).toFixed(2) + "Mbps，客户端到服务器平均路径长度为"+(data["averageLengthScore"]).toFixed(2)+"，实验测评得分是"+  data["finalScore"])
			location.reload()
			return
		}
	}, _this.errorHandler)
}

// 生成路由的整体评价
// 从外圈随机选取clientNum=(3/4)*outerNum个作为client，选取内圈1个作为server，设内圈路由传输速率为500Mbps，中圈速率为300Mbps，外圈为100Mbps
GameManager.prototype.initRouteEvaluation = function(data, needPaint) {
	if(data['status'] == 0){
		alert("路由表全为空，无法测试。需要有其中一人保存路由表才能进行测试")
		_this.secondStep();
		return -1
	}

	// defined
	var innerRate = 500
	var midRate = 300
	var outerRate = 150

	var outerNum = _this.topo.length - parseInt(_this.topo.length/3) * 2
	var clientNum = parseInt(outerNum * 3 / 4 + 1)
	var clientsIndex = []
	while(clientsIndex.length != clientNum){
		var tmp = _this.topo.length - 1 - parseInt(Math.random()*outerNum)
		if($.inArray(tmp, clientsIndex) == -1)
			clientsIndex.push(tmp)
	}
	var serverIndex = parseInt(Math.random()*parseInt(_this.topo.length/3))
	
	// 移除canvas元素和popup的DOM
	paper.project.activeLayer.removeChildren()
	$("table[id^=route-table]").remove()

	var p2pTopo = new Topology(data['scale']+outerNum, 0, 0)
	var c2sTopo = new Topology(data['scale']+outerNum, 0, 0)
	p2pTopo.avaliableLength = data['scale']
	c2sTopo.avaliableLength = data['scale']
	_this.topo = new Topology(data['scale'], 0, 0)

	var link = data['link']
	for(var i = 0; i < link.length; i++) {
		var tmp = link[i].split("-")
		_this.topo.matrix.link(tmp[0], tmp[1])
		p2pTopo.matrix.link(tmp[0], tmp[1])
		c2sTopo.matrix.link(tmp[0], tmp[1])
	}
	//连接客户端和对应的route节点
	for(var i in clientsIndex){
		p2pTopo.matrix.link(clientsIndex[i], clientsIndex[i]+outerNum)
		c2sTopo.matrix.link(clientsIndex[i], clientsIndex[i]+outerNum)
	}

	// 设计有误，则会回到第二步骤(查看和修改路由表)
	var error = []
	if(runRoute(_this.topo, data["route"], error) == false){
		alert("最新的路由表设计有误，" + error[0] +"--" + error[1] + "不通，请组内设计者修改")
		_this.secondStep();
		return -1
	}


	// 表示每个结点在P2P和C2S模式下的度数
	var routeP2PDegrees = new Array(_this.topo.length)
	for(var i=0; i<_this.topo.length; i++){
		routeP2PDegrees[i] = 0
	}
	var routeC2SDegrees = routeP2PDegrees.concat()
	var routeP2PAverageRate = routeP2PDegrees.concat()
	var routeC2SAverageRate = routeP2PDegrees.concat()
	var routeP2PPath = {}
	var routeC2SPath = {}

	// console.log("clientsIndex, serverIndex", clientsIndex, serverIndex)

	practiceRunRoute(_this.topo, data["route"], clientsIndex, serverIndex, routeP2PDegrees, routeP2PPath, routeC2SDegrees, routeC2SPath)
	// console.log(routeP2PDegrees)
	// console.log(routeP2PPath)
	// console.log("routeC2SDegrees" + routeC2SDegrees)
	// console.log(routeC2SPath)

	calculateAverageRate(routeP2PDegrees, routeP2PAverageRate, routeC2SDegrees, routeC2SAverageRate, innerRate, midRate, outerRate, parseInt(_this.topo.length/3), parseInt(_this.topo.length/3), outerNum)

	var routeP2PBottleneck = routeP2PAverageRate.concat()
	var routeC2SBottleneck = routeC2SAverageRate.concat()

	// console.log(routeP2PBottleneck)
	

	markBottleneck(_this.topo, data["route"], clientsIndex, serverIndex, routeP2PPath, routeP2PAverageRate, routeP2PBottleneck, routeC2SPath, routeC2SAverageRate, routeC2SBottleneck)
	// console.log("routeC2SBottleneck" + routeC2SBottleneck)

	if(needPaint){
		paintEvaluation(p2pTopo, c2sTopo, data["route"], clientsIndex, serverIndex, routeP2PAverageRate, routeP2PPath, routeP2PBottleneck, routeC2SAverageRate, routeC2SPath, routeC2SBottleneck, _this.routeTableScale);
		paper.project.activeLayer.view.update()
	}

	return getGrade(clientsIndex, serverIndex, routeC2SBottleneck, routeC2SPath)
}

// 得到client得到的平均transimission rate 和 path length的平均长度
var getGrade = function(clientsIndex, serverIndex, bottleneck, path){
	var tmpArr =[]
	var pathLength = []
	for(var i in clientsIndex){
		pathLength.push(path[clientsIndex[i]].length)
		tmpArr.push(bottleneck[clientsIndex[i]])
	}
	tmpArr = tmpArr.sort(function(a,b){
		return a - b
	});
	pathLength =  pathLength.sort(function(a,b){
		return a - b
	});
	var sum=0, pathSum = 0;
	for(var i = 1; i < tmpArr.length - 1; i++){
		sum+=tmpArr[i]
		pathSum+=pathLength[i]
	}
	return [sum/(tmpArr.length-2), pathSum/(pathLength.length-2)]
}

var calculateAverageRate = function(routeP2PDegrees, routeP2PAverageRate, routeC2SDegrees, routeC2SAverageRate, innerRate, midRate, outerRate, innerNum, midNum, outerNum){
	for(var i=0; i<routeP2PDegrees.length; i++){
		rate = 0
		if(i < innerNum){
			rate = innerRate
		} else if(i < innerNum+midNum) {
			rate = midRate
		}else{
			rate = outerRate
		}
		if(routeP2PDegrees[i] == 0)
			routeP2PAverageRate[i]=-1
		else 
			routeP2PAverageRate[i] = parseInt(rate / routeP2PDegrees[i])
		if(routeC2SDegrees[i] == 0)
			routeC2SAverageRate[i]=-1
		else 
			routeC2SAverageRate[i] = parseInt(rate / routeC2SDegrees[i])
	}
}

// 视频会议
var markBottleneck = function(topo, route, clientsIndex, serverIndex,  routeP2PPath, routeP2PAverageRate, routeP2PBottleneck, routeC2SPath, routeC2SAverageRate, routeC2SBottleneck) {
	
	// 计算routeP2PDegrees
	
	// 计算routeC2SDegrees
	for(var i in clientsIndex){
		if(clientsIndex[i] == serverIndex)continue
		var path = routeC2SPath[clientsIndex[i]]
		var bottleneckRate = routeC2SAverageRate[clientsIndex[i]]

		for(var j = 0; j < path.length; j++){
			if(routeC2SAverageRate[path[j]] < bottleneckRate){
				bottleneckRate = routeC2SAverageRate[path[j]]
			}
		}
		routeC2SBottleneck[clientsIndex[i]] = bottleneckRate
	}
}


// 视频会议
var practiceRunRoute = function(topo, route, clientsIndex, serverIndex, routeP2PDegrees, routeP2PPath, routeC2SDegrees, routeC2SPath) {
	// console.log(clientsIndex)
	// 计算routeP2PDegrees, 有错误。routeP2PPath的key应该是"clientsIndex[i]-clientsIndex[j]"的形式
	for(var i in clientsIndex) {
		for(var j in clientsIndex){
			if(i == j)continue
			var path = getPath(topo, route, clientsIndex[i], clientsIndex[j], topo.length - 1)
			routeP2PPath[clientsIndex[i]] = path
			routeP2PDegrees[clientsIndex[i]] ++
			for(var k = 0; k < path.length; k++){
				routeP2PDegrees[path[k]] ++
			}
		}
	}

	// 计算routeC2SDegrees
	for(var i in clientsIndex){
		if(clientsIndex[i] == serverIndex)continue
		// console.log("test:", clientsIndex[i], serverIndex)
		var path = getPath(topo, route, clientsIndex[i], serverIndex, topo.length - 1)
		routeC2SPath[clientsIndex[i]] = path
		routeC2SDegrees[clientsIndex[i]] ++
		for(var j = 0; j < path.length; j++){
			routeC2SDegrees[path[j]] ++
		}
	}
}

var getPath = function(topo, route, source, dest, maxLength) {
	var path = []
	var next = source
	for(var i=0; i<maxLength; i++) {
		next = getNext (topo, route, next, dest)
		path.push(next)
		if(next == -1){
			return []
		}
		if(next == dest){
			// console.log(path)
			return path
		}
	}
	return []
}

// 跑测试，从每个节点到任意节点是否通
var runRoute = function(topo, route, error) {
	// source = i, dest = j
	for(var i=0; i<topo.length; i++){
		for(var j=0; j< topo.length ; j++){
			if(j == i)
				continue
			if(isConnected(topo, route, i, j, topo.length-1) == false) {
				error.push(i)
				error.push(j)
				return false
			}
		}
	}
	return true
}

// source 和 dest之间是否能在路由上跑通
var isConnected = function(topo, route, source, dest, maxLength) {
	// console.log("source-dest:", source, dest)
	var path = []
	var next = source
	path.push(next)
	for(var i=0; i<maxLength; i++) {
		next = getNext (topo, route, next, dest)
		path.push(next)
		if(next == -1){
			// console.log("不通",path)
			return false
		}
		if(next == dest){
			// console.log("通", path)
			return true
		}
	}
	// console.log("不通", path)
	return false
}

var getNext = function(topo, route, localIndex, dest) {
	// 考虑是否在该节点有路由表的情况
	if(localIndex.toString() in route){
		routeTable = route[localIndex.toString()]
		for(var i=0; i< routeTable.length; i++){
			record = routeTable[i]
			for(var key in record) {
				if(key == "null")
					continue
				else if(key == "default") {
					next = parseInt(record[key])
					if(topo.matrix.isLinked(localIndex, next) == true){
						return next
					}
				} else {
					dests = key.split(",")
					next = parseInt(record[key])
					if($.inArray(dest.toString(), dests) != -1 && topo.matrix.isLinked(localIndex, next) == true){
						return next
					}
				}
			}

		}
		return -1
	} else
		return -1
}


// dest为null/default/逗号分割的数字，且数字在都节点索引内。next得是数字
var checkRouteRecord = function(dest, next, topoAvailableScale) {
	var regexp = new RegExp("^(\\d|,)*$","m")
	if(dest != "null" && dest != "default"){
		if(dest.match(regexp) == null)
			return -1
		else{
			nodes = dest.split(",")
			for(var index in nodes){
				if(nodes[index] == "")
					return -3
				node = parseInt(nodes[index])
				if(node >= topoAvailableScale || node < 0)
					return -2
			}
		}
	}
	if(next.match("^\\d+$") == null){
		return -1
	}
	return 0
}


GameManager.prototype.checkStatus = function(data) {
	if(data['status'] == "NA"){
		alert("您不在此实验可做日期之间，无法开始")
		return false
	}
	// 针对的是getTopo中的topo的status为CHOOSING
	if(data['status'] == -1){
		alert("实验记录已被某组员清除，实验重新开始，页面将会刷新")
		location.reload()
		return false
	}
	return true
}