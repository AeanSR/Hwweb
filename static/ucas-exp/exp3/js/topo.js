//当不使用随机位置生成时， height, width没有作用
function Topology(nodeNum, height, width) {
	this.height = height
	this.width = width
	this.matrix = new NodeMatrix(nodeNum, nodeNum)
	this.nodeList = new PointList(nodeNum, height, width)
	this.length = nodeNum
	// 代表实际节点书，evaluate的时候会在外层又加入一些点，这些不计入实际点
	this.avaliableLength = nodeNum
}
Topology.prototype.random = function() {
	this.matrix.randomLink()
}
function PointList(num, height, width) {
	function Point(x, y) {
		this.x = x
		this.y = y
	}
	// 点的位置随机，在画布渲染时进行固定
	this.value = new Array(num)
	for(var i = 0; i < num; i++) {
		this.value[i] = new Point(Math.random()*width, Math.random()*height)
	}
}
PointList.prototype.get = function(i) {
	return this.value[i]
}
PointList.prototype.set = function(i, x, y) {
	this.value[i].x = x
	this.value[i].y = y
}

function NodeMatrix(x, y) {
	var two_dimension = new Array(x)
	for(var i = 0; i < x; i++) {
		var row = new Array(y)
		for(j = 0; j < y; j++)
			row[j] = 0
		two_dimension[i] = row
	}
	this.value = two_dimension
}

NodeMatrix.prototype.put = function(i, j, v) {
	this.value[i][j] = v
}
NodeMatrix.prototype.get = function(i, j) {
	return this.value[i][j]
}
NodeMatrix.prototype.isLinked = function(i, j) {
	if (this.value[i][j] != 0)
		return true
	else
		return false
}
NodeMatrix.prototype.link = function(i, j) {
	this.value[i][j] = this.value[j][i] = 1
}
NodeMatrix.prototype.randomLink = function() {
	for(var i = 0; i < this.value.length; i++) {
		for(var j = 0; j < i; j++ ) {
			var tmp = Math.random() 
			if (tmp < 0.05)
				this.value[i][j] = this.value[j][i] = 1
			else
				this.value[i][j] = this.value[j][i] = 0
		}
	}
}
NodeMatrix.prototype.clearLink = function(i, j) {
	for(var i = 0; i < this.value.length; i++) {
		for(var j = 0; j <= i; j++ ) {
			this.value[i][j] = this.value[j][i] = 0
		}
	}
}

