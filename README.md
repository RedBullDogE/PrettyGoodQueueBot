# PrettyGoodQueueBot

Bot written with PyTelegramBotAPI and used to create simple small queues for some local events.

## Usage

QueueBot can be used only in group chats (for obvious reasons) and supports a few commands:

| command | Description |
| ------- | ----------- |
| /help   | Display help information |
| /create QUEUE_NAME | Create a new queue with specified name if it doesn't exist. Queue name is case insensitive. ONLY FOR CHAT ADMINISTRATORS. |
| /delete OR /remove QUEUE_NAME | Delete a queue if it exists. When using this command the bot just removes the possibility to enter/leave specified queue. The last state before removing queue is frozen FOREVER (until someone deletes this message). Queue nam is case insensitive. ONLY FOR CHAT ADMINISTRATORS. |
| /list   | Display existing queues in the chat |
| /find QUEUE_NAME | Find a queue in chat (answer is a reply message to specified queue) |

When the queue is created, each chat participant can enter and leave this queue by clicking the appropriate button. All chat members can take only one place in each queue. Leaving the chat does not affect queues.

### COMMANDS TODO
| command | Description |
| ------- | ----------- |
| /swap QUEUE_NAME TARGET_PLACE | Swap users at specified positions in the queue. Both users at specified places should use this command. |
| /delete_all | Delete all queues in the chat |
| /kick QUEUE_NAME PLACE | Kick user from specified position |

### BUGS
- cyrillic names are case sensetive (sqlite bug)
- exception with markdown parsing in enter/leave commands to queues with underline in name
- WHAT IF USER DELETE MESSAGE WITH QUEUE?


