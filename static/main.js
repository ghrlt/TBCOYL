$("form#delete-form").submit(function(e) {
	if(!confirm("Warning: You will lose access to all statistics of this link, and the link will no longer be accessible.\nTHIS ACTION IS DEFINITIVE AND CANNOT BE REVERSED")) {
		e.preventDefault();
	}
})