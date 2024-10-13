from langchain_core.messages import ToolMessage
from langchain_core.runnables import RunnableLambda 
from langchain_core.runnables import Runnable,RunnableConfig
from langgraph.prebuilt import ToolNode
from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph.message import AnyMessage, add_messages


def handle_tool_error(state)->dict:
    error=state.get('error')
    tool_call=state["messages"][-1].tool_calls
    return{

        "messages":[ToolMessage(content=f"Error:{repr(error)} please Fix this mistake .",
                                tool_call_id=tc["id"]) for tc in tool_call]
    }

def create_tool_node_with_fallback(tools: list) -> dict:
    return ToolNode(tools).with_fallbacks(
        [RunnableLambda(handle_tool_error)], exception_key="error"
    )

 


def _print_event(event: dict, _printed: set, max_length=5000):
    current_state = event.get("dialog_state")
    if current_state:
        print("Currently in: ", current_state[-1])
    message = event.get("messages")
    if message:
        if isinstance(message, list):
            message = message[-1]
        if message.id not in _printed:
            msg_repr = message.pretty_repr(html=True)
            if len(msg_repr) > max_length:
                msg_repr = msg_repr[:max_length] + " ... (truncated)"
            print(msg_repr)
            _printed.add(message.id)


from typing import Any








class State(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]







class Assistant:
    def __init__(self,runnable:Runnable) -> None:
        self.runnable=runnable


    def __call__(self, state:State,config:RunnableConfig):
        while True:
            configuration=config.get("configurable",{})
            user_id=configuration.get("user_id",None)
            state={**state ,"user_info":user_id}
            result=self.runnable.invoke(state)
            if not result.tool_calls and (
                not result.content
                or isinstance(result.content, list)
                and not result.content[0].get("text")
            ):
                messages = state["messages"] + [("user", "Respond with a real output.")]
                state = {**state, "messages": messages}
            else:
                break
        return {"messages": result}





