from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph.message import AnyMessage, add_messages
from utilities import *
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain.prompts import ChatPromptTemplate
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph, START
from langgraph.prebuilt import tools_condition

from Tools import lookup_policy,update_hotel_booking,create_room_booking,display_available_rooms,cancel_hotel_booking,fetch_user_hotel_information
from langchain_groq import ChatGroq


import os

# Setting the environment variable (for testing purposes)
os.environ['TAVILY_API_KEY'] = "tvly-"

llm=ChatGroq(api_key="",model="llama-3.2-11b-vision-preview")
primary_assistant_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a knowledgeable customer support assistant for a hotel booking system. "
            "Your role is to assist users with inquiries regarding room availability, booking processes, and cancellation requests. "
            "Be proactive in gathering essential information, such as check-in and check-out dates, room preferences, and the number of guests. "
            "If users have specific questions about hotel policies or services, provide clear and concise answers based on the hotel's guidelines. "
            "Guide users step-by-step through the booking process to ensure a smooth and efficient experience, addressing any issues they may encounter. "
            "If a search for available rooms or bookings returns no results, kindly encourage users to modify their criteria and search again. "
            "Your priority is to achieve user satisfaction by providing prompt, accurate, and helpful responses."
            "\n\nCurrent user:\n\n{user_info}\n"
        ),
        ("placeholder", "{messages}"),
    ]
)





class Graphing:
    def build(self):
        tools_of_chatbot=[
        TavilySearchResults(max_results=1),
        lookup_policy,
        update_hotel_booking,
        create_room_booking,
        display_available_rooms,
        cancel_hotel_booking,
        fetch_user_hotel_information,
        

    ]

        assiitant_runnable=primary_assistant_prompt| llm.bind_tools(tools_of_chatbot)
        builder=StateGraph(State)
        builder.add_node("assistant",Assistant(assiitant_runnable))
        builder.add_node("tools",create_tool_node_with_fallback(tools_of_chatbot))
        builder.add_edge(START,"assistant")
        builder.add_conditional_edges("assistant",tools_condition)
        builder.add_edge("tools","assistant")
        memory = MemorySaver()
        graph = builder.compile(checkpointer=memory)
        return graph



                    




