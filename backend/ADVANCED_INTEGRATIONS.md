# AAIS Advanced Integrations - Complete Implementation

## Overview

This guide covers 5 advanced integration features:
1. Slack integration
2. Discord integration
3. Zapier integration
4. Make integration
5. Custom API integration

---

## 1. Slack Integration

### Slack Integration System

```python
# src/integrations/slack_integration.py

import requests
import json
from typing import Dict, List
from datetime import datetime
from src.logger import get_logger

logger = get_logger(__name__)

class SlackIntegration:
    """Integrate AAIS with Slack"""
    
    def __init__(self, bot_token: str, signing_secret: str):
        self.bot_token = bot_token
        self.signing_secret = signing_secret
        self.api_url = 'https://slack.com/api'
    
    def send_message(self, channel: str, text: str, blocks: list = None) -> bool:
        """Send message to Slack channel"""
        logger.info(f"Sending message to Slack channel: {channel}")
        
        try:
            payload = {
                'channel': channel,
                'text': text
            }
            
            if blocks:
                payload['blocks'] = blocks
            
            response = requests.post(
                f"{self.api_url}/chat.postMessage",
                headers={'Authorization': f'Bearer {self.bot_token}'},
                json=payload
            )
            
            if response.status_code == 200:
                logger.info(f"Message sent successfully")
                return True
            else:
                logger.error(f"Failed to send message: {response.text}")
                return False
        except Exception as e:
            logger.error(f"Slack message failed: {e}")
            return False
    
    def send_ai_result(self, channel: str, prompt: str, result: str, model: str) -> bool:
        """Send AI generation result to Slack"""
        logger.info(f"Sending AI result to Slack")
        
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "🤖 AI Generation Result"
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Model:*\n{model}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Time:*\n{datetime.utcnow().isoformat()}"
                    }
                ]
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Prompt:*\n```{prompt}```"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Result:*\n```{result}```"
                }
            }
        ]
        
        return self.send_message(channel, "AI Generation Result", blocks)
    
    def handle_slash_command(self, command_data: dict) -> Dict:
        """Handle Slack slash command"""
        logger.info(f"Handling Slack slash command: {command_data.get('command')}")
        
        command = command_data.get('command')
        text = command_data.get('text')
        user_id = command_data.get('user_id')
        channel_id = command_data.get('channel_id')
        
        if command == '/generate':
            # Generate AI response
            result = self._generate_response(text)
            self.send_message(channel_id, f"Generated: {result}")
            return {'response_type': 'in_channel'}
        
        return {'response_type': 'ephemeral', 'text': 'Unknown command'}
    
    def _generate_response(self, prompt: str) -> str:
        """Generate AI response"""
        # Implementation would call actual AI model
        return f"Response to: {prompt}"
    
    def list_channels(self) -> List[Dict]:
        """List Slack channels"""
        logger.info("Listing Slack channels")
        
        try:
            response = requests.get(
                f"{self.api_url}/conversations.list",
                headers={'Authorization': f'Bearer {self.bot_token}'}
            )
            
            if response.status_code == 200:
                channels = response.json().get('channels', [])
                logger.info(f"Found {len(channels)} channels")
                return channels
            else:
                logger.error(f"Failed to list channels: {response.text}")
                return []
        except Exception as e:
            logger.error(f"Failed to list channels: {e}")
            return []
```

---

## 2. Discord Integration

### Discord Integration System

```python
# src/integrations/discord_integration.py

import discord
from discord.ext import commands
from typing import Dict, List
from datetime import datetime
from src.logger import get_logger

logger = get_logger(__name__)

class DiscordIntegration:
    """Integrate AAIS with Discord"""
    
    def __init__(self, bot_token: str):
        self.bot_token = bot_token
        self.bot = commands.Bot(command_prefix='!', intents=discord.Intents.default())
        self.setup_commands()
    
    def setup_commands(self):
        """Setup Discord bot commands"""
        logger.info("Setting up Discord commands")
        
        @self.bot.command(name='generate')
        async def generate(ctx, *, prompt: str):
            """Generate AI response"""
            logger.info(f"Discord generate command: {prompt}")
            
            async with ctx.typing():
                result = await self._generate_response(prompt)
                
                embed = discord.Embed(
                    title="🤖 AI Generation",
                    description=result,
                    color=discord.Color.blue(),
                    timestamp=datetime.utcnow()
                )
                embed.add_field(name="Prompt", value=prompt, inline=False)
                embed.add_field(name="Model", value="Mixtral-8x7B", inline=True)
                
                await ctx.send(embed=embed)
        
        @self.bot.command(name='help')
        async def help_command(ctx):
            """Show help"""
            embed = discord.Embed(
                title="AAIS Discord Bot",
                description="AI-powered generation bot",
                color=discord.Color.green()
            )
            embed.add_field(name="!generate <prompt>", value="Generate AI response", inline=False)
            embed.add_field(name="!help", value="Show this help message", inline=False)
            
            await ctx.send(embed=embed)
    
    async def send_message(self, channel_id: int, content: str, embed: discord.Embed = None) -> bool:
        """Send message to Discord channel"""
        logger.info(f"Sending message to Discord channel: {channel_id}")
        
        try:
            channel = self.bot.get_channel(channel_id)
            if channel:
                await channel.send(content, embed=embed)
                logger.info("Message sent successfully")
                return True
            else:
                logger.error(f"Channel not found: {channel_id}")
                return False
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            return False
    
    async def send_ai_result(self, channel_id: int, prompt: str, result: str, model: str) -> bool:
        """Send AI result to Discord"""
        logger.info("Sending AI result to Discord")
        
        embed = discord.Embed(
            title="🤖 AI Generation Result",
            color=discord.Color.blue(),
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="Model", value=model, inline=True)
        embed.add_field(name="Prompt", value=prompt, inline=False)
        embed.add_field(name="Result", value=result, inline=False)
        
        return await self.send_message(channel_id, "", embed=embed)
    
    async def _generate_response(self, prompt: str) -> str:
        """Generate AI response"""
        # Implementation would call actual AI model
        return f"Response to: {prompt}"
    
    def start(self):
        """Start Discord bot"""
        logger.info("Starting Discord bot")
        self.bot.run(self.bot_token)
    
    def list_servers(self) -> List[Dict]:
        """List Discord servers"""
        logger.info("Listing Discord servers")
        
        servers = []
        for guild in self.bot.guilds:
            servers.append({
                'id': guild.id,
                'name': guild.name,
                'members': guild.member_count
            })
        
        return servers
```

---

## 3. Zapier Integration

### Zapier Integration System

```python
# src/integrations/zapier_integration.py

import requests
import json
from typing import Dict, List
from src.logger import get_logger

logger = get_logger(__name__)

class ZapierIntegration:
    """Integrate AAIS with Zapier"""
    
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url
    
    def trigger_zap(self, event_type: str, data: Dict) -> bool:
        """Trigger Zapier workflow"""
        logger.info(f"Triggering Zapier workflow: {event_type}")
        
        try:
            payload = {
                'event_type': event_type,
                'timestamp': datetime.utcnow().isoformat(),
                'data': data
            }
            
            response = requests.post(
                self.webhook_url,
                json=payload,
                timeout=10
            )
            
            if response.status_code in [200, 201]:
                logger.info(f"Zapier workflow triggered successfully")
                return True
            else:
                logger.error(f"Failed to trigger Zapier: {response.text}")
                return False
        except Exception as e:
            logger.error(f"Zapier trigger failed: {e}")
            return False
    
    def on_generation_complete(self, user_id: int, prompt: str, result: str, model: str) -> bool:
        """Trigger on generation complete"""
        logger.info("Triggering on_generation_complete")
        
        return self.trigger_zap('generation_complete', {
            'user_id': user_id,
            'prompt': prompt,
            'result': result,
            'model': model
        })
    
    def on_user_signup(self, user_id: int, email: str, name: str) -> bool:
        """Trigger on user signup"""
        logger.info("Triggering on_user_signup")
        
        return self.trigger_zap('user_signup', {
            'user_id': user_id,
            'email': email,
            'name': name
        })
    
    def on_payment_received(self, user_id: int, amount: float, currency: str) -> bool:
        """Trigger on payment received"""
        logger.info("Triggering on_payment_received")
        
        return self.trigger_zap('payment_received', {
            'user_id': user_id,
            'amount': amount,
            'currency': currency
        })
    
    def on_error_occurred(self, error_type: str, error_message: str, user_id: int = None) -> bool:
        """Trigger on error"""
        logger.info("Triggering on_error_occurred")
        
        return self.trigger_zap('error_occurred', {
            'error_type': error_type,
            'error_message': error_message,
            'user_id': user_id
        })
```

---

## 4. Make Integration

### Make Integration System

```python
# src/integrations/make_integration.py

import requests
import json
from typing import Dict, List
from datetime import datetime
from src.logger import get_logger

logger = get_logger(__name__)

class MakeIntegration:
    """Integrate AAIS with Make (formerly Integromat)"""
    
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url
    
    def send_to_make(self, scenario_name: str, data: Dict) -> bool:
        """Send data to Make scenario"""
        logger.info(f"Sending data to Make scenario: {scenario_name}")
        
        try:
            payload = {
                'scenario': scenario_name,
                'timestamp': datetime.utcnow().isoformat(),
                **data
            }
            
            response = requests.post(
                self.webhook_url,
                json=payload,
                timeout=10
            )
            
            if response.status_code in [200, 201]:
                logger.info(f"Data sent to Make successfully")
                return True
            else:
                logger.error(f"Failed to send to Make: {response.text}")
                return False
        except Exception as e:
            logger.error(f"Make integration failed: {e}")
            return False
    
    def create_task(self, title: str, description: str, assignee: str = None) -> bool:
        """Create task in Make"""
        logger.info(f"Creating task in Make: {title}")
        
        return self.send_to_make('create_task', {
            'title': title,
            'description': description,
            'assignee': assignee
        })
    
    def send_email(self, to: str, subject: str, body: str) -> bool:
        """Send email via Make"""
        logger.info(f"Sending email via Make to: {to}")
        
        return self.send_to_make('send_email', {
            'to': to,
            'subject': subject,
            'body': body
        })
    
    def update_spreadsheet(self, spreadsheet_id: str, data: List[Dict]) -> bool:
        """Update Google Sheets via Make"""
        logger.info(f"Updating spreadsheet: {spreadsheet_id}")
        
        return self.send_to_make('update_spreadsheet', {
            'spreadsheet_id': spreadsheet_id,
            'data': data
        })
    
    def create_calendar_event(self, title: str, start_time: str, end_time: str) -> bool:
        """Create calendar event via Make"""
        logger.info(f"Creating calendar event: {title}")
        
        return self.send_to_make('create_calendar_event', {
            'title': title,
            'start_time': start_time,
            'end_time': end_time
        })
```

---

## 5. Custom API Integration

### Custom API Integration System

```python
# src/integrations/custom_api_integration.py

import requests
import json
from typing import Dict, List, Any
from datetime import datetime
from src.logger import get_logger

logger = get_logger(__name__)

class CustomAPIIntegration:
    """Integrate with custom APIs"""
    
    def __init__(self):
        self.integrations = {}
    
    def register_api(self, api_name: str, config: Dict) -> bool:
        """Register custom API"""
        logger.info(f"Registering custom API: {api_name}")
        
        try:
            # Validate configuration
            required_fields = ['base_url', 'auth_type']
            if not all(field in config for field in required_fields):
                logger.error("Missing required configuration fields")
                return False
            
            self.integrations[api_name] = {
                'config': config,
                'registered_at': datetime.utcnow().isoformat(),
                'status': 'active'
            }
            
            logger.info(f"API registered: {api_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to register API: {e}")
            return False
    
    def call_api(self, api_name: str, endpoint: str, method: str = 'GET', data: Dict = None) -> Dict:
        """Call custom API"""
        logger.info(f"Calling API: {api_name} - {endpoint}")
        
        if api_name not in self.integrations:
            logger.error(f"API not registered: {api_name}")
            return {'error': 'API not registered'}
        
        try:
            config = self.integrations[api_name]['config']
            url = f"{config['base_url']}{endpoint}"
            
            # Prepare headers
            headers = self._prepare_headers(config)
            
            # Make request
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=10)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=10)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=10)
            else:
                logger.error(f"Unsupported method: {method}")
                return {'error': 'Unsupported method'}
            
            if response.status_code in [200, 201]:
                logger.info(f"API call successful")
                return response.json()
            else:
                logger.error(f"API call failed: {response.status_code}")
                return {'error': response.text}
        except Exception as e:
            logger.error(f"API call failed: {e}")
            return {'error': str(e)}
    
    def _prepare_headers(self, config: Dict) -> Dict:
        """Prepare request headers"""
        headers = {'Content-Type': 'application/json'}
        
        auth_type = config.get('auth_type')
        
        if auth_type == 'bearer':
            headers['Authorization'] = f"Bearer {config.get('api_key')}"
        elif auth_type == 'api_key':
            headers['X-API-Key'] = config.get('api_key')
        elif auth_type == 'basic':
            import base64
            credentials = base64.b64encode(
                f"{config.get('username')}:{config.get('password')}".encode()
            ).decode()
            headers['Authorization'] = f"Basic {credentials}"
        
        return headers
    
    def list_integrations(self) -> List[Dict]:
        """List registered integrations"""
        logger.info("Listing registered integrations")
        
        integrations = []
        for api_name, api_data in self.integrations.items():
            integrations.append({
                'name': api_name,
                'status': api_data['status'],
                'registered_at': api_data['registered_at']
            })
        
        return integrations
    
    def test_connection(self, api_name: str) -> bool:
        """Test API connection"""
        logger.info(f"Testing connection to: {api_name}")
        
        if api_name not in self.integrations:
            logger.error(f"API not registered: {api_name}")
            return False
        
        try:
            config = self.integrations[api_name]['config']
            url = config['base_url']
            headers = self._prepare_headers(config)
            
            response = requests.get(url, headers=headers, timeout=5)
            
            if response.status_code < 500:
                logger.info(f"Connection successful")
                return True
            else:
                logger.error(f"Connection failed: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False
```

---

## 6. Integration with AAIS

### Integration API Endpoints

```python
# src/routes/integrations.py

from flask import Blueprint, request, jsonify
from src.integrations.slack_integration import SlackIntegration
from src.integrations.discord_integration import DiscordIntegration
from src.integrations.zapier_integration import ZapierIntegration
from src.integrations.make_integration import MakeIntegration
from src.integrations.custom_api_integration import CustomAPIIntegration
from src.logger import get_logger

logger = get_logger(__name__)

integrations_bp = Blueprint('integrations', __name__, url_prefix='/api/integrations')

# Initialize integrations
slack = SlackIntegration(bot_token='xoxb-...', signing_secret='...')
discord = DiscordIntegration(bot_token='...')
zapier = ZapierIntegration(webhook_url='https://hooks.zapier.com/...')
make = MakeIntegration(webhook_url='https://hook.make.com/...')
custom_api = CustomAPIIntegration()

# Slack endpoints
@integrations_bp.route('/slack/send', methods=['POST'])
def slack_send():
    """Send message to Slack"""
    data = request.json
    channel = data.get('channel')
    text = data.get('text')
    
    success = slack.send_message(channel, text)
    return jsonify({'success': success})

@integrations_bp.route('/slack/channels', methods=['GET'])
def slack_channels():
    """List Slack channels"""
    channels = slack.list_channels()
    return jsonify({'channels': channels})

# Discord endpoints
@integrations_bp.route('/discord/send', methods=['POST'])
async def discord_send():
    """Send message to Discord"""
    data = request.json
    channel_id = data.get('channel_id')
    content = data.get('content')
    
    success = await discord.send_message(channel_id, content)
    return jsonify({'success': success})

@integrations_bp.route('/discord/servers', methods=['GET'])
def discord_servers():
    """List Discord servers"""
    servers = discord.list_servers()
    return jsonify({'servers': servers})

# Zapier endpoints
@integrations_bp.route('/zapier/trigger', methods=['POST'])
def zapier_trigger():
    """Trigger Zapier workflow"""
    data = request.json
    event_type = data.get('event_type')
    event_data = data.get('data')
    
    success = zapier.trigger_zap(event_type, event_data)
    return jsonify({'success': success})

# Make endpoints
@integrations_bp.route('/make/send', methods=['POST'])
def make_send():
    """Send data to Make"""
    data = request.json
    scenario = data.get('scenario')
    payload = data.get('data')
    
    success = make.send_to_make(scenario, payload)
    return jsonify({'success': success})

# Custom API endpoints
@integrations_bp.route('/custom/register', methods=['POST'])
def register_custom_api():
    """Register custom API"""
    data = request.json
    api_name = data.get('api_name')
    config = data.get('config')
    
    success = custom_api.register_api(api_name, config)
    return jsonify({'success': success})

@integrations_bp.route('/custom/call', methods=['POST'])
def call_custom_api():
    """Call custom API"""
    data = request.json
    api_name = data.get('api_name')
    endpoint = data.get('endpoint')
    method = data.get('method', 'GET')
    payload = data.get('data')
    
    result = custom_api.call_api(api_name, endpoint, method, payload)
    return jsonify(result)

@integrations_bp.route('/custom/list', methods=['GET'])
def list_custom_apis():
    """List custom APIs"""
    integrations = custom_api.list_integrations()
    return jsonify({'integrations': integrations})

@integrations_bp.route('/custom/test/<api_name>', methods=['GET'])
def test_custom_api(api_name):
    """Test custom API connection"""
    success = custom_api.test_connection(api_name)
    return jsonify({'success': success})
```

---

## 7. Implementation Checklist

- [ ] Slack integration
- [ ] Discord integration
- [ ] Zapier integration
- [ ] Make integration
- [ ] Custom API integration
- [ ] API endpoints
- [ ] Event triggers
- [ ] Testing
- [ ] Documentation
- [ ] Deployment

---

## 8. Integration Benefits

### Slack
- Team collaboration
- Real-time notifications
- Slash commands
- Message formatting

### Discord
- Community engagement
- Bot commands
- Rich embeds
- Server management

### Zapier
- 5000+ app integrations
- Workflow automation
- No-code setup
- Reliable delivery

### Make
- Advanced workflows
- Conditional logic
- Data transformation
- Multi-step scenarios

### Custom API
- Unlimited flexibility
- Any service integration
- Custom authentication
- Full control

---

## Support

- Slack API: https://api.slack.com/
- Discord.py: https://discordpy.readthedocs.io/
- Zapier: https://zapier.com/
- Make: https://www.make.com/
- Requests: https://requests.readthedocs.io/
