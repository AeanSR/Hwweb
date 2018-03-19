function modAjax(){
	this.url = "/"
	this.times = 1
	this.mode = 1 // 默认为测试模式
	this.topoScale = 30
	this.result = "null"
	this.data = null
	this.finalGrade
}

modAjax.prototype.getinfo = function(on_Success,on_Error) {
	$.ajax({
		type:"POST",
		url:this.url+"api/route/getinfo",
		data:{
			mode:this.mode
		},
		dataType:"json",
		xhrFields: {
		    withCredentials: true
		},
		crossDomain: true,
		success:on_Success,
		error:on_Error
	})
};

modAjax.prototype.getTopo = function(on_Success,on_Error) {
	$.ajax({
		type:"POST",
		url:this.url+"api/route/getTopo",
		data:{	mode:this.mode,
			times: this.times,
			scale: this.topoScale
		},
		dataType:"json",
		xhrFields: {
		    withCredentials: true
		},
		crossDomain: true,
		success:on_Success,
		error:on_Error
	})
};

modAjax.prototype.submitTopo = function(on_Success,on_Error) {
	$.ajax({
		type:"POST",
		url:this.url+"api/route/submitTopo",
		data:{	mode:this.mode,
			topo: this.data,
			times:this.times
		},
		dataType:"json",
		xhrFields: {
		    withCredentials: true
		},
		crossDomain: true,
		success:on_Success,
		error:on_Error
	})
};

modAjax.prototype.submitRoute = function(on_Success,on_Error) {
	$.ajax({
		type:"POST",
		url:this.url+"api/route/submitRoute",
		data:{	mode:this.mode,
			times: this.times,
			route: this.result
		},
		dataType:"json",
		xhrFields: {
		    withCredentials: true
		},
		crossDomain: true,
		success:on_Success,
		error:on_Error
	})
};

//检测能否进入下一个实验
modAjax.prototype.checkStatus = function(on_Success,on_Error) {
	$.ajax({
		type:"GET",
		url:this.url+"api/route/submitResult",
		data:{	mode:this.mode,
			times: this.times
		},
		dataType:"json",
		xhrFields: {
		    withCredentials: true
		},
		crossDomain: true,
		success:on_Success,
		error:on_Error
	})
};

// 提交最终成绩
modAjax.prototype.submitRouteEvaluation = function(on_Success,on_Error) {
	$.ajax({
		type:"POST",
		url:this.url+"api/route/submitRouteEvaluation",
		data:{	mode:this.mode,
			score: this.score,
			times:this.times
		},
		dataType:"json",
		xhrFields: {
		    withCredentials: true
		},
		crossDomain: true,
		success:on_Success,
		error:on_Error
	})
};

// 提交最终成绩
modAjax.prototype.clearRouteRecordInTestMode = function(on_Success,on_Error) {
	$.ajax({
		type:"POST",
		url:this.url+"api/route/clearRouteRecordInTestMode",
		data:{	mode:this.mode
		},
		dataType:"json",
		xhrFields: {
		    withCredentials: true
		},
		crossDomain: true,
		success:on_Success,
		error:on_Error
	})
};
