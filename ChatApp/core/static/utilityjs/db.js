let db = new Localbase('messageDb');
db.config.debug = false
async function addToDatabase(messages_data){
    await db.collection('private_messages').add(messages_data);
}

async function getdbMessages(){
    var data = await db.collection('private_messages').get();
      console.log("get messages by thread",data)
      return data;
}
async function getMessagesById(m_id){
    var mydata = await db.collection('private_messages').doc({msg_id:parseInt(m_id)}).get();
    return mydata;
}