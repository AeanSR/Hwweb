function GameManager(mice, bottles, poisons,is_test, is_adversary) {
	this.mice = mice;
	this.bottles = bottles;
	this.orig_bottles = bottles;
	this.poisons = poisons;
	this.is_test =is_test
	this.is_adversary = is_adversary
	this.bottle_list = []
	this.active_bottle_list = {}
	this.poison_list = {}
	this.mouse_list = {}
	this.curBottles = 1
	this.steps = 0
	this.historys = {}
	this.historys['results'] = []
	this.submit_bottles = []
	this.curDragList = []
	this.popupClosed = true
	this.create();
};
GameManager.prototype.create = function() {
	var _this = this
	if(this.is_adversary){
		$('#header h1').text('Adaptive Game 1')
		$('#error-popup .ui-btn').attr('href','adaptive.html?testA')
		$('#best-scores').text('Best Steps:')
		this.totaltimes = 3
		this.Ajax = new modAjax(1,this)
	}
	else {
		$('#header h1').text('Adaptive Game 2')
		$('#error-popup .ui-btn').attr('href','adaptive.html?testN')
		$('#best-scores').text('Average Steps:')
		this.totaltimes = 5
		this.Ajax = new modAjax(4,this)
	}
	this.Ajax.getinfo(this.getSuccessHandler, this.getErrorHandler)
	//preload image
	new Image().src= 'imgs/mouse-dead.png'
	$(".submit").sortable()
	$("#bottles-container").sortable({
		start: function(event, ui) {
			_this.dragging = 'bottles'
			_this.curDragBottles = "bottles-" + ui.helper[0].id
			selectedDOMs = $("#" + _this.curDragBottles + ' .bottle')
			_this.curDragList = []
			for (var x = 0; x < selectedDOMs.length; x++) {
				_this.curDragList.push(parseInt(selectedDOMs[x].id))
			}
		}
	})
	// .droppable({
	// 	containment: "document",
	// 	appendTo: document.body,
	// 	accept: ".bottle",
	// 	drop: function(event, ui) {
	// 		console.log("Container dropped!")
	// 		if (!_this.popupOpen) {
	// 			_this.dropOnContainer = true
	// 		}
	// 	}
	// })
	$("#bottles-container").disableSelection();

	this.createRandomPoison()
	this.createEmptyBottles(this.curBottles);
	// Init data
	for (var i = 1; i <= this.bottles; i++) {
		this.bottle_list.push(i)
		this.active_bottle_list[i] = true
	}
	this.addToBottles(this.bottle_list, this.curBottles)
	this.curBottles += 1
	for (var i = 1; i <= this.mice; i++) this.mouse_list[i] = true
	this.createMice(this.mouse_list)

	$("#button_submit").click(function(event) {
		_this.Popup("#submit-popup")
	})
	$("#submit-popup .ui-btn").click(function(event) {
		var u_bottle = $("#input-bottle").val()
		if(u_bottle!=""){
			$("#submit-popup").popup("close")
			var c_bottle = []
			for(var bId in _this.active_bottle_list){
				if(_this.active_bottle_list[bId]){
					c_bottle.push(bId)
				}
			}
			//console.log("a", _this.is_Win)
			if(_this.is_adversary){
				if (c_bottle.length == 0){
					_this.isGameOver(false, u_bottle, -1)
				}
				else if(c_bottle.length == 1){
					var isCorrect =  u_bottle== c_bottle[0]
					_this.isGameOver(isCorrect, u_bottle, c_bottle[0])
				}
				else{
					u_bottle == c_bottle[0]?
					_this.isGameOver(false,u_bottle, c_bottle[1]):
					_this.isGameOver(false,u_bottle, c_bottle[0])
				}
			}
			else{
				var isCorrect = md5(u_bottle + "This is a salt~~!@@!")  in _this.poison_list
				if(isCorrect){
					_this.isGameOver(true, u_bottle, u_bottle)
				}else{
					u_bottle == c_bottle[0]?
					_this.isGameOver(false,u_bottle, c_bottle[1]):
					_this.isGameOver(false,u_bottle, c_bottle[0])
				}
			}

		}
	});

}
GameManager.prototype.getSuccessHandler = function(data) {
	name = data["name"]
	group = data["group"]
	GM.Ajax.gameLoop = data["curLoop"]
	if(GM.Ajax.gameLoop>GM.totaltimes-1 && !GM.is_test) {
		setTimeout(function(){
			$("#error-notice").html('<h3>Sorry, your challenges have been used up.But you can still play the test mode.</h3><a href="index.html" data-ajax="false" class="ui-btn ui-corner-all ui-shadow ui-btn-inline ui-btn-b" data-transition="flow">Back to the Guidance.</a>')
			$("#error-popup").popup("open")
		},1000)

	}
	$("#login_info").text("姓名：" + name + " 组号：" + group)
	$("#best-score").text(data["bestScore"])
	GM.setPanel()
}
GameManager.prototype.getErrorHandler = function() {
	setTimeout(function(){$("#error-popup").popup("open")},1000)
}
GameManager.prototype.putSuccessHandler = function(data) {
	if(data==true){
		$("#gameover .ui-btn").text("Continue")
	}
	else{
		$("#gameover .ui-btn").text("Retry(Submit Failed)")
	}
	$("#gameover .ui-btn").click(function() {
		location.href = newhref
	})
}
GameManager.prototype.putErrorHandler = function() {
	$("#gameover .ui-btn").text("Retry(Submit Failed)")
	$("#gameover .ui-btn").click(function() {
		location.href = newhref
	})
}
GameManager.prototype.setPanel = function() {
	if(this.is_test){
		$('#game-mode').text("Test Mode")
		$('#game-times').text("Unlimited")
		}
	else{
		$('#game-mode').text("Submit Mode")
		$('#game-times').text(this.totaltimes-GM.Ajax.gameLoop)
	}
}
GameManager.prototype.createRandomPoison = function() {
	for (var i = 0; i < this.poisons; i++) {
		poison = md5(Math.ceil(Math.random() *  this.bottles) + "This is a salt~~!@@!")
		//poison = md5(1 + "This is a salt~~!@@!")
		if (!(poison in this.poison_list)) {
			this.poison_list[poison] = 0;
		} else {
			i -= 1
		}
		poison = 0
	}

}

GameManager.prototype.createEmptyBottles = function(bottles_id) {
	var _this = this
	$("<div></div>", {
		class: "bottles",
		id: bottles_id
	})
		.html('<p>0</p><img src="imgs/bottles.png">')
		.attr('tested',false)
		.appendTo($("#bottles-container"))
	$("#bottles-container").sortable("refresh")
	//Dynamic append
	popup = $('<div></div>', {
		"data-role": "popup",
		id: "bottles-" + bottles_id,
		class: "bottle-popup"
	})
	.html('<div class="bottle-container"></div>')
	var page = $(':mobile-pagecontainer').pagecontainer('getActivePage');
	popup.appendTo(page).popup({"afterclose":function(){_this.popupClosed = true}})
	this.sorts = $("#bottles-" + bottles_id + " .bottle-container").selectable({
		handle: "#bottles-" + bottles_id + " .bottle-container",
		filter: ".bottle",
		distance:10,
		selected: function(event, ui) {
			$(ui.selected).draggable("enable")
			$(ui.selected).attr("select", true);
			$(ui.selected).css("background-color", "#356799");
		}
	});
	// TODO mobile axis
	$("#bottles-container #" + bottles_id).mousedown(function(event) {
		_this.mouse_move = false
	});
	$("#bottles-container #" + bottles_id).mousemove(function(event) {
		_this.mouse_move = true
	});
	$("#bottles-container #" + bottles_id).click(function(event) {
		// In case of firefox 
		if(!_this.mouse_move){
			//console.log('bottles ' + this.id + ' has been clicked')
			_this.popupClosed = false

				$("#bottles-" + this.id).css('visibility', 'visible')
				$("#bottles-" + this.id).popup("open", {
				x: event.pageX + 200,
				y: event.pageY + 150
			});

		}
	});
	$("#bottles-container #" + bottles_id).droppable({
		drop: function() {
			if($(this).attr("tested")=="false")
			_this.dropOnBottles = $(this)[0].id
		}
	})
}

GameManager.prototype.addToBottles = function(bottle_list, bottles) {
	for (var i in bottle_list) {

		$("<div></div>", {
			class: "bottle",
			id: bottle_list[i]
			})
		.attr("select", false)
		.html("<p>" + bottle_list[i] + "</p>" + '<img src="imgs/bottle.png">')
		.appendTo($("#bottles-" + bottles + " .bottle-container"))

		$("#bottles-" + bottles + " .bottle-container #" + bottle_list[i]).click(function() {
			if ($(this).attr("select") == "true") {
				$(this).attr("select", false);
				$(this).draggable("disable")
				$(this).css("background-color", "white");
			} else {
				$(this).attr("select", true);
				$(this).draggable("enable")
				$(this).css("background-color", "#356799");
			}
		})
		.draggable({
		containment: "#GameBoard",
		appendTo: "#GameBoard",
		distance: 20,
		start: function(event, ui) {
			_this.dragging = 'bottle'
			_this.dropOnContainer = false
			_this.dropOnBottles = 0
			_this.popupOpen = true
			ui.helper.attr("select", true);
			_this.curDragBottles = ui.helper.parent().parent()[0].id
			selectedDOMs = $("#" + _this.curDragBottles + ' .bottle[select=true]')
			_this.curDragList = []
			for (var x = 0; x < selectedDOMs.length; x++) {
				_this.curDragList.push(parseInt(selectedDOMs[x].id))
			}
			_this.popupOpen = false
			// Prevent bottle covered by the popup
			$("#"+ _this.curDragBottles).css('visibility', 'hidden')
			//$("#"+ _this.curDragBottles).popup("close")
			ui.helper.css('visibility',"visible")
			//this.popup = $("#"+ _this.curDragBottles)

		},
		stop: function(event, ui) {
			if (_this.dropOnMice || (_this.dropOnContainer && _this.dropOnBottles == 0)) {
				_this.removeFromBottles(_this.curDragList, _this.curDragBottles)
				if (_this.isBottlesEmpty(_this.curDragBottles) == true) _this.RemoveBottles(_this.curDragBottles)
				_this.createEmptyBottles(_this.curBottles)
				if (_this.NeedUpdate) _this.UsedBottles("bottles-" + _this.curBottles)
				_this.addToBottles(_this.curDragList, _this.curBottles)
				_this.curBottles += 1
			} else if (_this.dropOnBottles) {
				_this.removeFromBottles(_this.curDragList, _this.curDragBottles)
				if (_this.isBottlesEmpty(_this.curDragBottles) == true) _this.RemoveBottles(_this.curDragBottles)
				_this.addToBottles(_this.curDragList, _this.dropOnBottles)
			} else {
				_this.removeFromBottles(_this.curDragList, _this.curDragBottles)
				_this.addToBottles(_this.curDragList, _this.curDragBottles.split('-')[1])
			}
			if (!_this.popupOpen) {
				//console.log(_this.curDragBottles)
				$("#"+ _this.curDragBottles)
				$("#"+ _this.curDragBottles).popup('close')
				$("#"+ _this.curDragBottles).popup('close')
				$("#"+ _this.curDragBottles).popup('close')
				$("#"+ _this.curDragBottles).popup('close')
				$("#"+ _this.curDragBottles).popup('close')
				$("#"+ _this.curDragBottles).popup('close')
				$("#"+ _this.curDragBottles).popup('close')
				$("#"+ _this.curDragBottles).popup('close')
				$("#"+ _this.curDragBottles).popup('close')
				$("#"+ _this.curDragBottles).popup('close')
				$("#"+ _this.curDragBottles).popup('close')
				
			}

			_this.curDragBottles = undefined
			_this.curDragList = []
			_this.dropOnMice = false
			_this.dropOnBottles = false
			_this.dropOnContainer = false
			_this.NeedUpdate = false
		}
	}).draggable("disable")
	}
	this.UpdateBottles("bottles-" + bottles)
	//$("#bottle-container").sortable("refresh")
}

GameManager.prototype.removeFromBottles = function(bottle_list, bottles) {
	for (var x in bottle_list) {
		$('#' + bottles + " #" + bottle_list[x]).remove()
	}
	this.UpdateBottles(bottles)
}

GameManager.prototype.isBottlesEmpty = function(bottles) {
	if ($('#' + bottles + ' .bottle').length == 0) {
		return true
	} else {
		return false
	}
}

GameManager.prototype.RemoveBottles = function(bottles) {
	$('#bottles-container #' + bottles.split('-')[1]).remove()
}

GameManager.prototype.UpdateBottles = function(bottles) {
	target = $('#bottles-container #' + bottles.split('-')[1] + ' p')
	target.text($('#' + bottles + ' .bottle').length)
}

GameManager.prototype.UsedBottles = function(bottles) {
	target = $('#bottles-container #' + bottles.split('-')[1])
	target.css("background-color", "#356799")
	target.unbind()
	target.attr("tested",true)
	//this.bottles = this.bottles - 
}



GameManager.prototype.createMice = function(mouse_list) {
	_this = this
	for (var i in mouse_list) {
		$("<div></div>", {
			class: "mice",
			id: i
		})
			.html('<img src="imgs/mouse-alive.png">')
			.droppable({
				drop: function(event, ui) {
					_this.dropOnMice = $(this)[0].id
					mouse = $(this)[0].id
					// Is alive?
					if (_this.mouse_list[mouse]) {
						if (_this.dragging == 'bottles') {
							a = $('#bottles-container #' + _this.curDragBottles.split('-')[1])
							if(a.attr('tested')=="false"){
								if (!_this.testMice(_this.curDragList, mouse))
								_this.UsedBottles(_this.curDragBottles)
							}
						} else {
							if (_this.testMice(_this.curDragList, mouse)) {
								_this.UsedBottles(_this.curDragBottles)
							} else {
								_this.NeedUpdate = true
							}

						}
					}

				}
			})
			.appendTo($("#mice-container"))

	}
}
GameManager.prototype.testMice = function(bottles_list, mouse) {
	this.steps += 1
	gameModel = new AdaptiveAdversary()
	console.log('testing ' , this.bottles, bottles_list.length, this.mice)
	this.historys['results'].push(bottles_list.toString() + ' to mouse ' + mouse)
	$('#SubmitBoard #step-score').html(this.steps)
	if(this.is_adversary){
		if(gameModel.computerDecide(this.bottles, bottles_list.length, this.mice)[0]){
			// if (bottles_list.length == 1) {
			// 	flag = true
			// 	for (var x in this.submit_bottles) {
			// 		if (bottles_list[0] == this.submit_bottles[x]) flag = false
			// 	}
			// 	if (flag) {
			// 		$("#gameover .result").append("<p>" + bottles_list[0] + "</p>")
			// 		this.submit_bottles.push(bottles_list[0])
			// 	}

			// }
			this.mouse_list[mouse] = false
			$("#mice-container #" + mouse)
				.animate() //Animate here
			.html('<img src="imgs/mouse-dead.png">')
			//this.isGameOver()
			delete GameModel
			this.bottles = bottles_list.length
			for(var x in this.active_bottle_list){
				if ($.inArray(parseInt(x),bottles_list)==-1) this.active_bottle_list[x] = false
				else this.active_bottle_list[x] = true
			}
			this.mice = this.mice - 1
			if(this.mice==0&&this.bottles>1)this.isGameOver(false,-1,-1)
			//console.log(this.bottles)
			return true
		}
		$("#mice-container #" + mouse)
			.animate() //Animate here
		delete GameModel
		// Kick off the healthy bottles
		this.bottles = this.bottles - bottles_list.length
		for(var x in this.active_bottle_list){
			if($.inArray(parseInt(x),bottles_list)!=-1){
				this.active_bottle_list[x] = false
			}
		}
		//console.log(this.bottles)
		return false
	}
	else{
		found =false
		for(var k in bottles_list){
			poison = md5(bottles_list[k]+ "This is a salt~~!@@!") 
			if(poison in this.poison_list){
				found = true
			}
		}
		if(found){
			// if (bottles_list.length == 1) {
			// 	flag = true
			// 	for (var x in this.submit_bottles) {
			// 		if (bottles_list[0] == this.submit_bottles[x]) flag = false
			// 	}
			// 	if (flag) {
			// 		$("#gameover .result").append("<p>" + bottles_list[0] + "</p>")
			// 		this.submit_bottles.push(bottles_list[0])
			// 	}

			// }
			this.mouse_list[mouse] = false
			$("#mice-container #" + mouse)
				.animate() //Animate here
			.html('<img src="imgs/mouse-dead.png">')
			//this.isGameOver()
			delete GameModel
			this.bottles = bottles_list.length
			for(var x in this.active_bottle_list){
				if ($.inArray(parseInt(x),bottles_list)==-1) this.active_bottle_list[x] = false
				else this.active_bottle_list[x] = true
			}
			this.mice = this.mice - 1
			if(this.mice==0&&this.bottles>1)this.isGameOver(false,-1,-1)
			return true
		}
		$("#mice-container #" + mouse)
			.animate() //Animate here
		delete GameModel
		// Kick off the healthy bottles
		this.bottles = this.bottles - bottles_list.length
		for(var x in this.active_bottle_list){
			if ($.inArray(parseInt(x),bottles_list)!=-1) this.active_bottle_list[x] = false
		}

		console.log(this.bottles)
		return false
	}

}


GameManager.prototype.isGameOver = function(isCorrect, u_bottle, c_bottle) {
	this.historys['submit'] = {"user":u_bottle,"correct":c_bottle}

	this.is_test?
	newhref = 'adaptive.html?test':
	newhref = 'adaptive.html?submit'
	this.is_adversary?
	newhref += 'A':
	newhref += 'N'
	if(u_bottle==-1){
		$("#gameover-result").text("All mice are dead.")
	}else
	$("#gameover-result").text("The poisoned bottle is " + c_bottle + ", your answer is bottle " + u_bottle)
	if (isCorrect) {
		$("#gameover h1").text("Great!")
		$("#gameover #gameover-notice").text("You have passed the game successfully with " + this.steps + " steps!")
		this.is_test?
		$("#gameover #gameover-content").text("Test mode won't upload the results."):
		$("#gameover #gameover-content").text("The result will be submitted to the server. ")
		if(this.is_test){
			$("#gameover .ui-btn").text("Retry")
			$("#gameover .ui-btn").click(function() {
				location.href = newhref
			})
		}
		else{
			$("#gameover .ui-btn").text("Uploading...")
			this.Ajax.putinfo(this.steps,this.historys,
				this.putSuccessHandler,this.putErrorHandler)
		}

		this.Popup("#gameover")
		return
	}
	else {
		$("#gameover h1").text("Sorry!")
		$("#gameover #gameover-notice").text("You lose the game!")
		this.is_test?
		$("#gameover #gameover-content").text("Test mode won't upload the results."):
		$("#gameover #gameover-content").text("The result will be submitted to the server. The steps will be conunted as the number of bottles.")
		if(this.is_test){
			$("#gameover .ui-btn").text("Retry")
			$("#gameover .ui-btn").click(function() {
				location.href = newhref
			})
		}
		else{
			$("#gameover .ui-btn").text("Uploading...")
			this.Ajax.putinfo(this.orig_bottles,this.historys,
				this.putSuccessHandler,this.putErrorHandler)
		}
		this.Popup("#gameover")	
	}
	

}
GameManager.prototype.Popup = function(selector) {
	console.log(_this.popupClosed)
	_this = this
		if(_this.popupClosed)
		{	
			_this.popupClosed =false
			$(selector).popup({
				afteropen:function(){
					_this.popupClosed = false
				},
				afterclose:function(){
					_this.popupClosed = true
				}
			})
			.popup("open")
		}
		else{
			setTimeout(function(){_this.Popup(selector)}, 500)
			return		
		}
}
function AdaptiveAdversary() {
	this.mat=[]
    	for(var i=0;i<101;++i)this.mat[i]=[0,0,0]
}
AdaptiveAdversary.prototype.computerDecide = function(bottles, selectedbottles, mice) {
	if(bottles==selectedbottles)return [1,this.humanDecide(selectedbottles,mice-1)];
	var a=this.humanDecide(bottles-selectedbottles,mice);
	var b=this.humanDecide(selectedbottles,mice-1);
	if(a>=b)return [0,a];
	return [1,b];
}
AdaptiveAdversary.prototype.humanDecide = function(bottles,mice){     
    		if(bottles==1)return 0;
    		if(mice==0){
    			if(bottles>1)return 65535
    			return 0
    		}
    		if(mice==1){
    			return bottles-1
    		}
    		if(this.mat[bottles][mice]!=0){
    			return this.mat[bottles][mice]
    		}
    		var min=65535
    		var ind=0
    		for (var i=1;i<=bottles;++i){
    			
    			var t1=this.computerDecide(bottles,i,mice)
    			var t=t1[1]
    			if(t<min){
    				min=t
    				ind=i

    			}
    		}
    		this.mat[bottles][mice]=min+1
    		return min+1;
    }
$(function() {
	if ((index = location.href.search('#')) != -1) {
		location.href = location.href.substr(0,index)
		return
	}
	$("body").iealert();
	if (location.href.search('/?submitA') != -1) {
		alert("This is a sumbit mode. You should be careful to submit your results.")
		GM = new GameManager(2, 32, 1,false, true);

	}
	else if(location.href.search('/?submitN') != -1){
		alert("This is a sumbit mode. You should be careful to submit your results.")
		GM = new GameManager(2, 32, 1,false, false);
	}
	else if(location.href.search('/?testA') != -1){
		GM = new GameManager(2, 16, 1,true, true);
	}
	else if(location.href.search('/?testN') != -1){
		GM = new GameManager(2, 16, 1,true, false);
	}
	else{
		console.log('Input error.')
	}
});
