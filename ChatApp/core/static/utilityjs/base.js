const Toast = Swal.mixin({
	toast: true,
	position: 'top-end',
	showConfirmButton: false,
	timer: 3000,
	timerProgressBar: true,
	didOpen: (toast) => {
	  toast.addEventListener('mouseenter', Swal.stopTimer)
	  toast.addEventListener('mouseleave', Swal.resumeTimer)
	}
  })
  



function preloadCallback(src, elementId){
    var img = document.getElementById(elementId)
    img.src = src
}


function preloadImage(imgSrc, elementId){
    // console.log("attempting to load " + imgSrc + " on element " + elementId)
    var objImagePreloader = new Image();
    objImagePreloader.src = imgSrc;
    if(objImagePreloader.complete){
        preloadCallback(objImagePreloader.src, elementId);
        objImagePreloader.onload = function(){};
    }
    else{
        objImagePreloader.onload = function() {
            preloadCallback(objImagePreloader.src, elementId);
            //    clear onLoad, IE behaves irratically with animated gifs otherwise
            objImagePreloader.onload=function(){};
        }
    }
}




// var hljs = require('highlight.js');
function validateText(str)
	{   
		var md = window.markdownit({
			highlight: function (str, lang) {
				if (lang && hljs.getLanguage(lang)) {
					try {
						return '<pre class="hljs"><code>' +
							hljs.highlight(lang, str, true).value +
							'</code></pre>';
					} catch (__) {}
				}
				return '<pre class="hljs"><code>' + md.utils.escapeHtml(str) + '</code></pre>';
			},
			linkify: true,
		});
		var result = md.render(str);
		return result
	}

	var setPageNumber = (pageNumber)=>{
		document.getElementById('page_number_id').innerHTML = pageNumber;
	}

	let hexString = "0123456789abcdef";
	let randomColor = () => {
		let hexCode = "#";
		for( i=0; i<6; i++){
			hexCode += hexString[Math.floor(Math.random() * hexString.length)];
		}
		return hexCode;
	}
	
	let generateGrad = (elem) => {
		let colorOne = randomColor();
		let colorTwo = randomColor();
		let angle = Math.floor(Math.random() * 360);
		elem.style.background = `linear-gradient(${angle}deg, ${colorOne}, ${colorTwo})`;
		elem.value = `background: linear-gradient(${angle}deg, ${colorOne}, ${colorTwo});`;
	}
	function clearChat(){
		document.getElementById('id_chat_log').innerHTML='';
		let randomColor = Math.floor(Math.random()*16777215).toString(16);
		// generateGrad(document.getElementById('id_chat_log'));
	}
	
	var paginationKhattam = ()=>{
		setPageNumber("-1");
	}

	function escapeHTML (unsafe_str) {
		return unsafe_str
		  .replace(/&/g, '&amp;')
		  .replace(/</g, '&lt;')
		  .replace(/>/g, '&gt;')
		  .replace(/\"/g, '&quot;')
		  .replace(/\'/g, '&#39;')
		  .replace(/\//g, '&#x2F;')
	}
	
	function appendChatMessage(data,maintainPosition,test_skey){
		key = document.getElementById('topbar_otheruser_name').dataset.val;
		msg_id= data['msg_id'];
		(async() => {

		var temp_messages;

		temp_messages = await getMessagesById(msg_id);
		if(temp_messages!=undefined){
			encrypted_message_content = temp_messages['message_content'];
		message_content = decrypt(escapeHTML(encrypted_message_content),test_skey);
		user_id = temp_messages['user_id'];
		sender_fname = data['first_name'];
		sender_lname = data['last_name'];
		msg_timestamp = data['natural_timestamp'];
		profile_image = temp_messages['profile_image'];
		username = temp_messages['username'];
		
		//get the parent ul element
		var chat_history = document.getElementById('id_chat_log');
		
		//create the child elements
		var newMessageBlock = document.createElement('div');
		var conversation_list_div = document.createElement('div');
		var chat_avatar_div = document.createElement('div');
		var user_chat_content_div = document.createElement('div');
		var ctext_wrap_div = document.createElement('div');
		var ctext_wrap_content_div = document.createElement('div');
		var new_message_content = document.createElement('p');
		var message_timestamp_p = document.createElement('p');
		var conversation_name_div = document.createElement('div');
	
		//add class to every created element
		conversation_list_div.classList.add('conversation-list');
		chat_avatar_div.classList.add('chat-avatar');
		user_chat_content_div.classList.add('user-chat-content');
		ctext_wrap_div.classList.add('ctext-wrap');
		ctext_wrap_content_div.classList.add('ctext-wrap-content');
		new_message_content.classList.add('mb-0')
		message_timestamp_p.classList.add('chat-time','mb-0');
		conversation_name_div.classList.add('conversation_name_div');
		var profileImage = document.createElement('img');
		profileImage.dataset.sender_id = user_id;
		profileImage.classList.add('clickable_cursor');
		profileImage.src = profile_image;
		profileImage.addEventListener('click',(e)=>{
			selectUser(profileImage.dataset.sender_id);
		});
		var sender_profile_image_id = "sender_profile_image_"+msg_id;
		profileImage.id = sender_profile_image_id;
		//rewrite the content of the created element message,timestamp and name
		new_message_content.innerHTML = validateText(message_content);
		message_timestamp_p.innerHTML = msg_timestamp
		conversation_name_div.innerHTML = sender_fname +" "+ sender_lname
		//check if the sender is the logged in user
			//append elements in order
			ctext_wrap_content_div.append(new_message_content,message_timestamp_p);
			ctext_wrap_div.appendChild(ctext_wrap_content_div);
			user_chat_content_div.append(ctext_wrap_div,conversation_name_div);
			chat_avatar_div.appendChild(profileImage);
			conversation_list_div.append(chat_avatar_div,user_chat_content_div)
			newMessageBlock.appendChild(conversation_list_div)
		if(user_id == logged_user.id && username == logged_user.username){
			// new_message_content.classList.add('')
			newMessageBlock.classList.add('sent','right');
	
		}else{
			// new_message_content.classList.add('')
			newMessageBlock.classList.add('replies');
		}
		//append message based on if it is instant message or the whole chunk of previous messages
	chat_history.appendChild(newMessageBlock);
	if(!maintainPosition){
		scrollToBottom();
	}
	}
	})()

	}

	function appendNewChatMessage(data,maintainPosition,isNewMessage,test_skey){
		msg_id= data['msg_id'];
		user_id = data['user_id'];
		encrypted_message_content = data['message_content']
		message_content = decrypt(escapeHTML(encrypted_message_content),test_skey);
		// console.log("encrypted msg",encrypted_message_content);
		// console.log("decrypted msg ",message_content);
		sender_fname = data['first_name'];
		sender_lname = data['last_name'];
		msg_timestamp = data['natural_timestamp'];
		profile_image = data['profile_image'];
		username = data['username'];
		
		//get the parent ul element
		var chat_history = document.getElementById('id_chat_log');
		
		//create the child elements
		var newMessageBlock = document.createElement('div');
		var conversation_list_div = document.createElement('div');
		var chat_avatar_div = document.createElement('div');
		var user_chat_content_div = document.createElement('div');
		var ctext_wrap_div = document.createElement('div');
		var ctext_wrap_content_div = document.createElement('div');
		var new_message_content = document.createElement('p');
		var message_timestamp_p = document.createElement('p');
		var conversation_name_div = document.createElement('div');
	
		//add class to every created element
		conversation_list_div.classList.add('conversation-list');
		chat_avatar_div.classList.add('chat-avatar');
		user_chat_content_div.classList.add('user-chat-content');
		ctext_wrap_div.classList.add('ctext-wrap');
		ctext_wrap_content_div.classList.add('ctext-wrap-content');
		new_message_content.classList.add('mb-0')
		message_timestamp_p.classList.add('chat-time','mb-0');
		conversation_name_div.classList.add('conversation_name_div');
		var profileImage = document.createElement('img');
		profileImage.dataset.sender_id = user_id;
		profileImage.classList.add('clickable_cursor');
		profileImage.addEventListener('click',(e)=>{
			selectUser(profileImage.dataset.sender_id);
		});
		var sender_profile_image_id = "sender_profile_image_"+msg_id;
		profileImage.id = sender_profile_image_id;
		//rewrite the content of the created element message,timestamp and name
		new_message_content.innerHTML = (validateText(message_content));
		message_timestamp_p.innerHTML = msg_timestamp
		conversation_name_div.innerHTML = sender_fname +" "+ sender_lname
		//check if the sender is the logged in user
			//append elements in order
			ctext_wrap_content_div.append(new_message_content,message_timestamp_p);
			ctext_wrap_div.appendChild(ctext_wrap_content_div);
			user_chat_content_div.append(ctext_wrap_div,conversation_name_div);
			chat_avatar_div.appendChild(profileImage);
			conversation_list_div.append(chat_avatar_div,user_chat_content_div)
			newMessageBlock.appendChild(conversation_list_div)
		if(user_id == logged_user.id && username == logged_user.username){
			// new_message_content.classList.add('')
			newMessageBlock.classList.add('sent','right');
	
		}else{
			// new_message_content.classList.add('')
			newMessageBlock.classList.add('replies');
		}
		//append message based on if it is instant message or the whole chunk of previous messages
	
		if(isNewMessage){
			chat_history.insertBefore(newMessageBlock,chat_history.firstChild);
		}else{
			chat_history.appendChild(newMessageBlock);
		}
		if(!maintainPosition){
			scrollToBottom();
		}
		preloadImage(profile_image,sender_profile_image_id);
	}

	function scrollToBottom(){
		$('#id_chat_log').scrollTop($('#id_chat_log').prop("scrollHeight"));
	}

	const loader = document.querySelector('.loader')
	const hideLoader = () => {
		loader.classList.remove('show');
	};

	const showLoader = () => {
		loader.classList.add('show');
	};
	function displayChatroomLoadingSpinner(isDisplayed){
		if(isDisplayed){
			loader.classList.add('show');
		}
		else{
			loader.classList.remove('show');
		}
	}
	// $('#is_typing').hide();

	// function displayTyping(typing){
	// 	console.log("typing value",typing)
	// 	if(typing){
	// 		console.log("show typing")
	// 		$('#is_typing').show();
	// 		displayTyping(false)
	// 	}else{
	// 		$('#is_typing').hide();
	// 	}
	// }

	var enableChatHistoryScroll = ()=>{
		$('#id_chat_log').on('scroll',chatHistoryScroll);
	}
	
	var disableChatHistoryScroll = ()=>{
		$('#id_chat_log').off('scroll',chatHistoryScroll);
	}

	function setActiveThreadFriend(userId){
		t = document.getElementById('id_friend_list_'+userId)
		if(t!=null){
		t.parentElement.classList.add('active');
		}else{
			console.log("t is null");
		}
	}
	
	function showClientErrorModal(message){
		document.getElementById("id_client_error_modal_body").innerHTML = message
		document.getElementById("id_trigger_client_error_modal").click()
	}
	

//for updating thread list view
function update_thread_list_view(data){
	var logged_user =JSON.parse(document.getElementById('logged_in_user').textContent);

	var ulist = document.getElementById('contact_list_ul');
	ulist.innerHTML = ''
	data['chat_threads'].forEach(thread => {
	if(thread.first_user || thread.second_user){
		if(thread.first_user.username ===logged_user['username']){
		var myhtml = `<li class="myclass">
						<a onclick="onSelectFriend('${thread.second_user.id}',this);" data-threadType="private-thread"  data-userId="${thread.second_user.id}" id="id_friend_list_${thread.second_user.id}">
							<div class="d-flex">                            
								<div class="chat-user-img online align-self-center me-3 ms-0">
									<img id="id_friend_img_${thread.second_user.id}" src="${thread.second_user.profile_image}" class="rounded-circle avatar-sm" alt="">
									<!-- <span class="user-status"></span> -->
								</div>
		
								<div class="flex-1 overflow-hidden">
									<h5 class="text-truncate text-white font-size-15 mb-1">${thread.second_user.first_name} ${thread.second_user.last_name}</h5>
									<p class="chat-user-message pvt-chat-message-list text-white text-truncate mb-0" msgid="${thread.last_msg.id}" ></p>
								</div>
								<div class="font-size-11">05 min</div>
							</div>
						</a>
					</li>`
			ulist.innerHTML += myhtml
		}else{
		var myhtml = `<li class="myclass">
						<a onclick="onSelectFriend('${thread.first_user.id}',this);" data-threadType="private-thread" data-userId="${thread.first_user.id}" id="id_friend_list_${thread.first_user.id}">
							<div class="d-flex">                            
								<div class="chat-user-img online align-self-center me-3 ms-0">
									<img id="id_friend_img_${thread.first_user.id}" src="${thread.first_user.profile_image}" class="rounded-circle avatar-sm" alt="">
									<!-- <span class="user-status"></span> -->
								</div>
		
								<div class="flex-1 overflow-hidden">
									<h5 class="text-truncate text-white font-size-15 mb-1">${thread.first_user.first_name} ${thread.first_user.last_name}</h5>
									<p class="chat-user-message pvt-chat-message-list text-white text-truncate mb-0" msgid="${thread.last_msg.id}" ></p>
								</div>
								<div class="font-size-11">05 min</div>
							</div>
						</a>
					</li>`
			ulist.innerHTML += myhtml
		}
	}else{
		var myhtml = `<li class="myclass">
						<a onclick="onSelectGroup('${thread.id}',this);" data-threadType="group-thread" data-userId="${thread.id}" id="id_friend_list_${thread.id}">
							<div class="d-flex">                            
								<div class="chat-user-img online align-self-center me-3 ms-0">
									<img id="id_friend_img_${thread.id}" src="${thread.image}" class="rounded-circle avatar-sm" alt="">
									<!-- <span class="user-status"></span> -->
								</div>
		
								<div class="flex-1 overflow-hidden">
									<h5 class="text-truncate text-white font-size-15 mb-1">${thread.group_name}</h5>
									<p class="chat-user-message text-white text-truncate mb-0">${escapeHTML(thread.latest_msg)}</p>
								</div>
								<div class="font-size-11">05 min</div>
							</div>
						</a>
					</li>`
			ulist.innerHTML += myhtml
	}
	})
}

// $('#test_api').on('click',function(){
// 	$.ajax({
// 		type:"GET",
// 		url: window.location.origin+'/chat/test_api/',
// 		success: (data)=>{
// 			console.log("chat threads list",data)
// 		},
// 		error:(error_data)=>{
// 			console.log(error_data);
// 		},

// 	})
// })

function gk(){
	var shk =JSON.parse(document.getElementById('keys').textContent);
	var users_id = $("a[data-threadType='private-thread']").map(function(){
		return $(this).data('userid');
	}).get();
	var csrf = document.getElementsByName('csrfmiddlewaretoken')[0].value;
	$.ajax({
		type:"POST",
		url: window.location.origin+'/chat/gsk/',
        dataType: "json",
		data:{
			'users_id':users_id,
			'csrfmiddlewaretoken':csrf,		},
		success: (data)=>{
			console.log("gk ko data",data)

			set_thread_list_messages(data['ks']);
		},
		error:(error_data)=>{
			console.log(error_data);
		},

	})
}
var shk =JSON.parse(document.getElementById('keys').textContent);

function set_thread_list_messages(s = shk){
	$("a[data-threadType='private-thread'] p").filter(async function(i){
		var msgids = $(this).attr('msgid');
			thread_list_messages = await getMessagesById(msgids);
			// console.log(thread_list_messages);
			// console.log(thread_list_messages['message_content'],s[i]);
			if(thread_list_messages!=undefined){
				$(this).html(decrypt(thread_list_messages['message_content'],s[i]));	
			}
	});
};


const getMessagesByThread = (t_id)=>{
	var t_m = getdbMessages();
	console.log("not showing tm",t_m)
	var msg_data,my_msg;
	my_msg = t_m.then(collection=>{
		if(collection!=undefined){
			msg_data = filter_msg(collection,'private_thread_id',t_id);
			return msg_data;
		}else{
			return [];
		}
	});
	console.log("my msg of get message",my_msg);
	return my_msg;
}

const filter_msg = (messages_chunk,field,field_value)=>{
	var filtered_data = [];
	messages_chunk.forEach(element => {
		if(element[field] == field_value){
			filtered_data.push(element);
		}
	});
	return filtered_data;
}


	//for encryption and decryption
	const XOREncryptDecrypt = (message, keyString) => {
		const key = keyString.split("");
		const output = [];
		for (let i = 0; i < message.length; i++) {
			const charCode =
				message.charCodeAt(i) ^ key[i % key.length].charCodeAt(0);
			output.push(String.fromCharCode(charCode));
		}
		return output.join("");
	};
	
	const encrypt = (message, key) =>
		XOREncryptDecrypt(message, key);

	const decrypt = (encryptedMessage, key) =>
		XOREncryptDecrypt(encryptedMessage, key);


		$ (function () {
			endpoint = 'ws: //127.0.0.1: 8000 / new-user /' // 1
	
			var socket = new ReconnectingWebSocket (endpoint) // 2
			
		   // 3
			socket.onopen = function (e) {
			  console.log ("open", e); 
			}
			socket.onmessage = function (e) {
			  console.log ("message", e)
			}
			socket.onerror = function (e) {
			  console.log ("error", e)
			}
			socket.onclose = function (e) {
			  console.log ("close", e)
			}
	   });
	
	 $ (function () {
			endpoint = 'ws://localhost:8000/new-user/' // 1
	 
			var socket = new ReconnectingWebSocket (endpoint) // 2
			
		   // 3
			socket.onopen = function (e) {
			  console.log ("open", e); 
			}
			socket.onmessage = function (e) {
			  console.log ("message", e)
			}
			socket.onerror = function (e) {
			  console.log ("error", e)
			}
			socket.onclose = function (e) {
			  console.log ("close", e)
			}
	   });

