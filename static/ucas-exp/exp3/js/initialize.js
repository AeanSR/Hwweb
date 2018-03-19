$(document).on("pagecreate", function(){
	$("body").iealert();
	if(location.href.search('/?formal') != -1){
		gm = new GameManager("formal")
		$("#gameMode").text("Formal-Mode")
	}
	else{
		gm = new GameManager("test")
		$("#gameMode").text("Test-Mode")
	}
	gm.getinfo()
})