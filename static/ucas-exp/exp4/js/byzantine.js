var READY = 1;
var NOT_READY = 0;

//天气
var WEATHERS = 3;
var SUNNY = 0;
var RAINY = 1;
var CLOUDY = 2;
var weahterList = ["晴天","雨天","多云"]

var LIUBEI = "刘备";
var ZHANGFEI = "张飞";
var ZHAOYUN = "赵云";
var GUANYU = "关羽";
var ZHUGELIANG = "诸葛亮";
var HUANGZHONG = "黄忠"

function Army(){
	this.globalTime = 0;
	this.transferCondition = {}   // 定义转换为Ready的条件表达式, 后经eval判断
	//  上下文
	this.generalName =  LIUBEI      // 将领名称
	this.troops =  5000     // 5000人
	this.weahter =  SUNNY       // SUNNY:晴天, RAINY:雨天, CLOUDY: 雪天
	this.supply =  5000	//  粮食斤数
}

Army.prototype.chkReady = function(){

	evalStr = "" +
	"this.supply" + this.transferCondition['supply'][0] + this.transferCondition['supply'][1] + '&&' +
	"this.troops" + this.transferCondition['troops'][0] + this.transferCondition['troops'][1] + '&&' +
	"this.weahter" + "==" + this.transferCondition['weahter'][1];
	return eval(evalStr)
}
Army.prototype.chkCorrect = function(){
	var n = 0;
	if(this.transferCondition && this.transferCondition!={} && GM.everSetCond==true) n++    // 1
	var newDAG = jQuery.extend(true, {}, DAG)
	// 2
	if('army-mainBody' in newDAG){
		delete newDAG['army-mainBody']
		n++
	}
	// 3
	if('mainBody-weather' in newDAG){
		delete newDAG['mainBody-weather']
		n++
	}
	// 4
	if('food-mainBody' in DAG){
		delete newDAG['food-mainBody']
		n++
	}
	// 5
	if('food-timer' in DAG){
		delete newDAG['food-timer']
		n++
	}
	// 6
	if('food-randomer' in DAG){
		delete newDAG['food-randomer']
		n++
	}
	// 7
	if('army-timer' in DAG){
		delete newDAG['army-timer']
		n++
	}
	// 8
	if('army-randomer' in DAG){
		delete newDAG['army-randomer']
		n++
	}
	// 9
	if('timer-weather' in DAG){
		delete newDAG['timer-weather']
		n++
	}
	// 10
	if('randomer-weather' in DAG){
		delete newDAG['randomer-weather']
		n++
	}

	if($.map(newDAG, function(n, i) { return i; }).length!=0){
		n =-1  //dummy
	}
	// 11
	if(numInBody == 6){
		n++;
	}
	console.log('correct:',n)
	if(n==10 && GM.everSetCond==false) alert("还没有设置内部逻辑，请点击部队模块设置转移条件，设置完成后请务必点击设置界面的确定按钮。")
	if(n==11)return true
	else return false
}


function GameManager(submitMode){
	var _this = this
	this.day = 0
	this.everAttack = false
	this.submitMode = submitMode
	this.testUser = false
	this.everSetCond = false
	if(submitMode)
	$("#titles").text("系统角度实验:三国战役(提交模式)")
	else
	$("#titles").text("系统角度实验:三国战役(测试模式)")
	this.army = new Army()
	//DONE
	this.namemap = [LIUBEI,ZHANGFEI,ZHAOYUN,GUANYU,ZHUGELIANG,HUANGZHONG]
	this.restTime = 0
	this.Ajax = new modAjax(5,this);
	this.Ajax.getinfo(this.getSuccessHandler, this.getErrorHandler);
	this.sock = new SockJS('/api/exp4');

	this.sock.onopen = function() {
	     console.log('Established the connection.');
	     _this.sock.send(_this.getLoginJson(_this.userId,_this.submitMode))
	};
	this.sock.onmessage = function(e) {
	     console.log('message', e.data);
	     var msg = $.parseJSON(e.data)
	     if(msg['data_type'] == 'notify'){
	     	if(msg['data']['event'] == 'start'){
	     		setTimeout(function(){$("#pause-popup").popup("close")},500)
	     		_this.day = msg['data']['day']
	     		_this.playersList = msg['data']['playersList']
	     		_this.playersListMaps = _this.getPlayerMaps()
	     		_this.log("",'人员就位，游戏开始，今天是第' + _this.day + '天。' , 'sys')
	     		_this.interval = parseInt(msg['data']['interval'])
	     		_this.startTimer()
	     		_this.sync(true)
	     		_this.report()
	     	}
	     	else if(msg['data']['event'] == 'end'){
	     		setTimeout(function(){$("#pause-popup").popup("close")},500)
	     		setTimeout(function(){$("#end-popup").popup("open")},1000)
	     	}
	     	else if(msg['data']['event'] == 'sync'){	
	     		_this.day = msg['data']['day']
	     		_this.identity = msg['data']['identity']
	     		_this.playersList = msg['data']['playersList']
	     		_this.playersListMaps = _this.getPlayerMaps()
	     		_this.log("",'新的一天到来，今天是第' + _this.day + '天。' , 'sys')
	     		_this.sync(false)
	     		_this.report()
	     		_this.startTimer()
	     	}
	     	else if(msg['data']['event'] == 'gameresult'){
	     		if(msg['data']['win'] ){
	     			_this.log("",'今天平安渡过，所有将军做出了正确的决策。' , 'sys')
	     		}
	     		else{
	     			_this.log("",'败仗！看来我们之中出了一个叛徒。' , 'sys')
	     		}
	     	}
	     }
	     else if(msg['data_type'] == 'update'){   
	     	_this.userlist = msg['data']
	     	$('#userlist ul').text("")
	     	for(var userId in _this.userlist){
	     		_this.userlist[userId]['online']?
	     		$('#userlist ul').append('<li><span style="color:green">' + _this.userlist[userId]['name'] + '</span></li>'):
	     		$('#userlist ul').append('<li><span style="color:grey">' + _this.userlist[userId]['name']  + '</span></li>')
	     	}
	     	_this.log("",msg['event']==true?"有人加入了游戏":"有人离开了游戏，游戏暂停。" , 'sys')
	     	if(msg['event']==false && _this.stage == 1){
	     		$("#pause-popup").popup("open")
	     	}
	      }
	     else if(msg['data_type'] == 'message'){
	     	_this.log(msg['from'],msg['data'],'game')
	     }
	     else if(msg['data_type'] == 'attack'){
	     	// _this.log("",msg['data']==true?"有人发起攻击":"有人拒绝攻击",'attack')
	     	// setAttack(parseInt(msg['from']),msg['data'])
	     	_this.log("","刚刚有人做出了决策。",'sys')
	     }
	     else if(msg['data_type'] == 'auth'){
	     	if(msg['data']['notify']=='success'){
	     		_this.id = parseInt(msg['data']['id'])
	     		_this.testUser =  msg['data']['test']
	     		_this.identity = msg['data']['identity']
	     		_this.numPlayers = msg['data']['numPlayers']
	     		if(_this.numPlayers == 1){
	     			_this.numPlayers = 5
	     		}
	     		_this.messages = msg['data']['messages']
	     		_this.ready = msg['data']['ready']
	     		_this.name = _this.namemap[_this.id]
	     		_this.stage = msg['data']['stage']
	     		_this.army.transferCondition = msg['data']['cond']
	     		_this.army.troops = msg['data']['resource']['troops']
	     		_this.army.supply = msg['data']['resource']['supply']
	     		_this.army.weahter = msg['data']['resource']['weahter']
	     		_this.initStage2()
	     		if(_this.stage==0){
	     			_this.initStage1()
	     		}
	     		else{
	     			_this.moveStage2()
	     		}
	     		
	     		//_this.sock.send(_this.getMsgJson(0,{"generalname":_this.name},'register'))
	     	}
	     }
	};
	this.sock.onclose = function() {
		console.log('close');
	};
}

GameManager.prototype.getNameList = function(){
	u = []
	for(var user in this.userlist){
		u.push(this.userlist[user]["name"])
	}
	return u
}
GameManager.prototype.getPlayerMaps = function(){
	var maps = {}
	var i = 0
	for(var id in this.playersList){
		maps[this.playersList[id]] = i
		i++
	}
	return maps
}
GameManager.prototype.initStage2 = function(){
	_this = this
	$('#current-messages').text(_this.messages)
 	$('#receivers').html('<input type="checkbox" name="all" id="c1-all" data-mini="true"><label for="c1-all">全部</label>')
 	$('#send-content').text("")
 	var x=0;
 	for(var x=0;x<_this.numPlayers;x++){
 		if(x!=_this.id){
 			var html ='<input type="checkbox" name="'+ x +'" id="c1-' + x + '" data-mini="true"><label for="c1-'+ x + '">'+ _this.namemap[x] + '</label>'
 			$('#receivers').append(html)
 		}
 		$('#receivers').trigger('create')
 		var html = ''
			+ '<fieldset class="ui-grid-a" name="' + x + '">'
			+ '<div class="ui-block-a">'
		    + '<input type="checkbox" name="'+ x +'" id="checkbox-' +x + '" data-mini="true">'
		    + '<label for="checkbox-' + x +'">'+ _this.namemap[x] + '</label>'
			+ '</div>'
		    + '<div class="ui-block-b">'
		    + '<select id="flipswitch-'+ x + '" style="position:relative" data-role="flipswitch"><option value="NOT_READY">等待</option><option value="READY">就绪</option></select>'
			+ '</div>'
			+ '</fieldset>'
  		$('#send-content').append(html)
 	}
 	$('#receivers').trigger('create')
 	$('#send-content').trigger('create')

	$('#confirm-send').click(function(){
		var receivers = []
		var sendContent = {}
		$('#receivers input').each(function(x,y){
			if($(y).prop('name')!='all' && $(y).prop('checked')){
				receivers.push($(y).prop('name'))
			}
		})
		$('#send-content input').each(function(x,y){
			if($(y).prop('checked')){
				sendContent[$(y).prop('name')] = $($('#send-content select')[x]).val()
			}
		})
		if(receivers.length>0){
			_this.sock.send(_this.getMsgJson(receivers, sendContent, 'message'))
			_this.log(_this.id,sendContent,'game',receivers)
			_this.messages += receivers.length
			$('#current-messages').text(_this.messages)
		}

	});
	$('#attack').click(function(){
		_this.everAttack=true
		_this.sock.send(_this.getMsgJson(0, {'decide':true, 'messages':_this.messages}, 'attack'))
	})
	$('#notattack').click(function(){
		_this.everAttack=false
		_this.sock.send(_this.getMsgJson(0, {'decide':false, 'messages':_this.messages}, 'attack'))
	})
	$('#hides').click(function(){
		if($("#traitor-status").css('display')=='block'){
			$("#traitor-status").css('display','none')

		}
		else{
			$("#traitor-status").css('display','block')
		}
			
	})
}

GameManager.prototype.moveStage2 = function(){
	$('#console-stage1').css('display','none')
	$('#control-stage1').css('display','none')
	$('#console-stage2').css('display','block')
	$('#control-stage2').css('display','block')
	setTimeout(function(){$("#pause-popup").popup("open")},500)
	_this.waitPaperjs("initStep2")
}

GameManager.prototype.initStage1 = function(){
	_this = this
	$('#console-stage1').css('display','block')
	$('#control-stage1').css('display','block')
	$("#confirm-condition").click(function(){
		if(parseInt($("#food-val").val())!=NaN && parseInt($("#troops-val").val())!=NaN){
			_this.army.transferCondition = {'supply':[$("#food-op").val()=="smaller"?"<=":">",parseInt($("#food-val").val())],
			'troops':[$("#troops-op").val()=="smaller"?"<=":">",parseInt($("#troops-val").val())],
			'weahter':['==',$("#weather-val").val()]}
			_this.everSetCond = true
			// "this.ready = " +
			// "this.supply" + ($("#food-op").val()=="smaller"?"<=":">") + parseInt($("#food-val").val()) + '&&' +
			// "this.troops" + ($("#troops-op").val()=="smaller"?"<=":">") + parseInt($("#troops-val").val()) + '&&' +
			// "this.weahter" + "==" + $("#weather-val").val();
		}
	})
	$('#make').click(function(){
		if(_this.army.chkCorrect()){
			var r=confirm("构建成功，是否要保存截图？若保存，请再弹出的新标签页中右键图片保存，然后再返回本标签页。截图可用于实验报告中。")
			if(r==true){
				var dataURL = document.getElementById("canvas").toDataURL('image/png');
				window.open(dataURL, "_blank");
			}
			_this.log('','部队构建完毕，等待战斗！','sys')
			_this.sock.send(_this.getMsgJson(0, {"cond":_this.army.transferCondition}, 'nextstage'))
			_this.moveStage2()
			_this.stage = 1
		}
		else{
			_this.log('','部队一盘散沙，不能成军，请重下军令！','sys')

		}
	})
	$('#clean').click(function(){
		_this.waitPaperjs("initStep1")
		_this.everSetCond = false
	})
	if(_this.testUser){
		$('#jump').css("display","block")
		$('#jump').click(function(){
			_this.log('','部队构建完毕，等待战斗！','sys')
			_this.sock.send(_this.getMsgJson(0, {"cond":_this.army.transferCondition}, 'nextstage'))
			_this.moveStage2()
			_this.stage = 1
		})
	}

	_this.waitPaperjs("initStep1")
}

GameManager.prototype.startTimer = function(){
	_self = this
	this.restTime = this.interval;
	if(this.resttimer){
		clearInterval(this.resttimer)
		this.resttimer = undefined
	}
	this.resttimer = setInterval(function(){
		if(_self.restTime>=0){
			_self.restTime -=1;
			$('#rest-time').text(_self.restTime + '秒')
			}
		},1000)
}


GameManager.prototype.getLoginJson = function(userId,submitMode){
	return JSON.stringify({
	    "data_type": "login",
	    "data": {
	    	"userId": userId,
	    	"submitMode":submitMode
    	}})
}


GameManager.prototype.getMsgJson = function(to, data, type){
	return JSON.stringify({
	    "data_type": type,
	    "to": to ,
	    "data": data
	})
}

GameManager.prototype.getSuccessHandler = function(data) {
	GM.name = data["name"]
	GM.group = data["group"]
	GM.userId = data["userId"]
	$("#login_info").text("姓名：" + GM.name + " 组号：" + GM.group)
}
GameManager.prototype.getErrorHandler = function() {
	setTimeout(function(){$("#error-popup").popup("open")},1000)
}

GameManager.prototype.newStatus = function(ready){
	var newResource = {}
	var range = 1000
	var maxTimes = 100
	var times = 0
	var cond = this.army.transferCondition
	if(ready){
		this.ready = true
	}else{
		this.ready = false
	}
	var thresTroops = cond['troops'][1]
	var thresSupply = cond['supply'][1]
	var oldTroops = this.army.troops
	var oldSupply = this.army.supply

	while(true){
		this.army.troops = Math.floor(thresTroops - range + Math.random()*range*2)
		this.army.supply = Math.floor(thresSupply - range + Math.random()*range*2)
		this.army.weahter = Math.floor(Math.random()*WEATHERS)
		times += 1
		if(this.army.chkReady()== this.ready || times >= maxTimes) break

	}
}
GameManager.prototype.sync = function(isStart){
	// 新的一天到来，或者刚开局，重新渲染界面
	oldTroops = this.army.troops
	oldSupply = this.army.supply
	oldWeather = this.army.weahter
	if(!isStart){
		var randnum = Math.random()
		if(randnum>0.5){
			this.newStatus(true)
		}
		else{
			this.newStatus(false)
		}
		
		diffTroops = this.army.troops - oldTroops
		diffSupply = this.army.supply - oldSupply
		loseTroops = diffTroops<=0?Math.abs(diffTroops):(Math.floor(Math.abs(diffTroops)*0.2 + Math.random(Math.floor(Math.abs(diffTroops)*0.2))))
		addTroops = diffTroops<=0?0:(diffTroops + loseTroops)
		useSupply = diffSupply<=0?Math.abs(diffSupply):Math.floor(oldTroops * 0.1)
		addSupply = diffSupply<=0?0:(diffSupply + useSupply)
		console.log(diffTroops,diffSupply)
		str = ""
		if(this.everAttack){
			str += "由于昨天发动了攻击，兵力损失了" + loseTroops + '人, 新募集士兵' + addTroops + '人；'
		}
		else{
			str += "由于昨天未进行攻击，兵力因伤病损失了" + loseTroops + '人, 新募集士兵' + addTroops + '人；'
		}
		str += "供给士兵消耗粮食" + useSupply + "斤，" + "同时新增补给粮食" + addSupply + "斤；"
		str += '今天天气是' + weahterList[this.army.weahter] + '。'
		this.log('',str,'sys')
		this.everAttack = false

	}
	else{
		this.log('',('现有兵力')+ this.army.troops + '人，' +
		('现有粮食') + this.army.supply + '斤，' +
		'今天天气是' + weahterList[this.army.weahter] + '。','sys')
	}
	this.ready = this.army.chkReady()
	this.log('', "将军根据设定条件判断，" + (this.ready?"军队为就绪状态，战斗胜算较大。":"军队为整备状态，战斗胜算较小。"),'sys')
	this.ready?$("#ready-status").text("已经就绪"):$("#ready-status").text("整备中")
	$('#resource-status').text(this.army.troops+ '/'+ this.army.supply + '/' + weahterList[this.army.weahter])
	this.waitPaperjs("resetStep2")

	standbyId = 0+1+2+3+4+5;
	for(var i=0; i<this.playersList.length; i++) standbyId -= parseInt(this.playersList[i]);
	for(var i=0; i<this.numPlayers; i++) {
		if (i == standbyId){
			$('#c1-'+i).prop('checked', false).checkboxradio("refresh")
			$('#c1-'+i).attr('disabled', 'disabled')
			$('#c1-'+i).parent().css('display','none')

			$('#checkbox-'+i).prop('checked', false).checkboxradio("refresh")
			$('#checkbox-'+i).attr('disabled', 'disabled')
			$('#checkbox-'+i).parent().parent().parent().css('display','none')

			//$('#flipswitch'+i).parent().parent().css('display','none')
		} 
		else{
			$('#c1-'+i).removeAttr('disabled')	
			$('#c1-'+i).prop('checked', false).checkboxradio("refresh")	
			$('#c1-'+i).parent().css('display','block')

			$('#checkbox-'+i).removeAttr('disabled')
			$('#checkbox-'+i).prop('checked', false).checkboxradio("refresh")	
			$('#checkbox-'+i).parent().parent().parent().css('display','block')

			//$('#flipswitch'+i).parent().parent().css('display','block')
		}
	}
	$('#c1-all').prop('checked', false).checkboxradio("refresh")
	

	$('#c1-all').click(function(){
		$('#receivers input').each(function(x,y){
			if($(y).prop('name')!='all' && $(y).prop('name')!= $('#c1-'+standbyId).prop('name') ){
				$(y).prop('checked',$('#c1-all').prop('checked')).checkboxradio("refresh")
			}
		})
 	}) 

	$("#current-day").text(this.day)
	$('#traitor-status').text(this.identity=='loyal'?"忠臣":(this.identity=='traitor'?"内奸":"旁观者"))
	if(this.identity == 'standby'){
		setTimeout(function(){$("#standby-popup").popup("open")},1000)
	}
	else{
		setTimeout(function(){$("#standby-popup").popup("close")},500)
	}
}
GameManager.prototype.report = function(){
	this.sock.send(this.getMsgJson(0,{'troops':this.army.troops,'supply':this.army.supply,'weahter':this.army.weahter,"ready":this.ready},'report'))
}
GameManager.prototype.log = function(from,message, type, receiver){
	control = $("#log")
	if(type=='sys'){
		control.append('<span style="color:blue">系统通知: </span>' + message + '<br/>')
	}
	else if(type=='game'){
		var fromMaps = this.playersListMaps[from]
		var from = parseInt(from)
		var tar = []
		var t
		for(r in receiver){
			t = parseInt(receiver[r])
			tar.push(this.namemap[t])
		}
		var targetMaps
		var target
		// DONE
		if(from<this.numPlayers){
			var text = []
			for(var i in message){
				targetMaps = this.playersListMaps[i]
				target = parseInt(i)
				text.push(this.namemap[target] + "->" + ((message[i]=='READY')?"就绪":"整备中"))
				console.log('a',from,target,fromMaps,targetMaps)
				setStep2(fromMaps,targetMaps,message[i]=='READY')			
			}
			if(tar.length>0)
			control.append('<span style="color:green">' + this.namemap[from] + ':</span>' + '发送给 => ' + tar.join(",") +", 消息是 => "+ text.join(",") + '<br/>')
			else
			control.append('<span style="color:green">' + this.namemap[from] + ':</span>' + '发送给 => 你 '+", 消息是 => "+ text.join(",") + '<br/>')
			// edges[]

		}
		else{
			console.log('Unknwon User')
		}
	}
	// else if (type=='attack'){
	// 	control.append('<span style="color:green">' + this.namemap[from] + ':</span>' + message + '<br/>')
	// }
	control.scrollTop(control[0].scrollHeight);
}
GameManager.prototype.id2name = function(id){
	return this.userlist[id]['name']
}
GameManager.prototype.name2id = function(id){
	return null
}
GameManager.prototype.waitPaperjs = function(fun) {
	_this = this
	ok = false
	try{
		if(initStep1&&resetStep2){
			ok = true
		}
	}catch(e){
		
	}
		if(ok)
		{	
			if(fun=="initStep1")
			{
				initStep1(_this.id)
			}
			else if (fun=="initStep2"){
				initStep2(_this.id)
			}
			else if(fun=="resetStep2"){
				resetStep2(_this.id,_this.playersList)
			}
		}
		else{
			setTimeout(function(){_this.waitPaperjs(fun)}, 500)
			return		
		}
}
$(function(){
	if ((index = location.href.search('#')) != -1) {
		location.href = location.href.substr(0,index)
		return
	}
	if (location.href.search('/?submit') != -1) {
		alert("这里是提交模式，您应该谨慎操作。")
		GM = new GameManager(true);

	}
	else if(location.href.search('/?test') != -1){
		GM = new GameManager(false);
	}
	else{
		alert("你不应该来这儿的。")
	}
});


