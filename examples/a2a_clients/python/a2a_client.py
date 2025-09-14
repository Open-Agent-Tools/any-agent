#!/usr/bin/env python3
"""
A2A Client Example Script

This script demonstrates how to interact with an A2A server running on http://localhost:8035/
Based on the A2A Protocol tutorial: https://a2a-protocol.org/latest/tutorials/python/6-interact-with-server/
"""

import asyncio
import httpx
from a2a.client import ClientFactory, A2ACardResolver, ClientConfig
from a2a.client.helpers import create_text_message_object


async def main():
    """Main function to demonstrate A2A client interaction."""
    base_url = "http://localhost:8045/"

    print(f"Connecting to A2A server at {base_url}")

    async with httpx.AsyncClient() as httpx_client:
        try:
            # Step 1: Fetch Agent Card
            print("Fetching agent card...")
            resolver = A2ACardResolver(httpx_client=httpx_client, base_url=base_url)
            agent_card = await resolver.get_agent_card()
            print(f"Successfully fetched agent card: {agent_card.name}")

            # Step 2: Initialize A2A Client using ClientFactory
            print("Initializing A2A client...")
            client_config = ClientConfig(httpx_client=httpx_client)
            factory = ClientFactory(config=client_config)
            client = factory.create(card=agent_card)

            # Step 3: Send a message using the new Client interface
            print("\n--- Sending message ---")
            message_text = "Hello! Can you help me with a simple task?"

            # Create message using helper function
            message = create_text_message_object(content=message_text)

            print(f"Sending message: {message_text}")

            # Send message and iterate through responses
            async for response in client.send_message(message):
                if hasattr(response, "model_dump"):
                    print(
                        f"Response: {response.model_dump(mode='json', exclude_none=True)}"
                    )
                else:
                    print(f"Response: {response}")

            # Step 4: Send another message
            print("\n--- Sending second message ---")
            second_message_text = "Can you explain the A2A protocol in simple terms?"

            second_message = create_text_message_object(content=second_message_text)

            print(f"Sending message: {second_message_text}")

            async for response in client.send_message(second_message):
                if hasattr(response, "model_dump"):
                    print(
                        f"Response: {response.model_dump(mode='json', exclude_none=True)}"
                    )
                else:
                    print(f"Response: {response}")

        except httpx.HTTPError as e:
            print(f"HTTP error occurred: {e}")
        except Exception as e:
            print(f"An error occurred: {e}")


if __name__ == "__main__":
    print("A2A Client Example")
    print("==================")
    asyncio.run(main())
