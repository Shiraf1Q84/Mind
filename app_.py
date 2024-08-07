# app.py
import os
import streamlit as st
from datetime import datetime

from lagent.actions import ActionExecutor, BingBrowser

from mindsearch.agent.models import internlm_server
from mindsearch.agent.mindsearch_agent import (MindSearchAgent,
                                               MindSearchProtocol)
from mindsearch.agent.mindsearch_prompt import (
    FINAL_RESPONSE_CN, FINAL_RESPONSE_EN, GRAPH_PROMPT_CN, GRAPH_PROMPT_EN,
    fewshot_example_cn, fewshot_example_en, graph_fewshot_example_cn,
    graph_fewshot_example_en, searcher_context_template_cn,
    searcher_context_template_en, searcher_input_template_cn,
    searcher_input_template_en, searcher_system_prompt_cn,
    searcher_system_prompt_en)


LLM = {}


def init_agent(lang='ja', model_format='internlm_server'):
    llm = LLM.get(model_format, None)
    if llm is None:
        llm_cfg = getattr(internlm_server, model_format)
        if llm_cfg is None:
            raise NotImplementedError
        llm_cfg = llm_cfg.copy()
        llm = llm_cfg.pop('type')(**llm_cfg)
        LLM[model_format] = llm

    interpreter_prompt = GRAPH_PROMPT_CN if lang == 'cn' else GRAPH_PROMPT_EN
    plugin_prompt = searcher_system_prompt_cn if lang == 'cn' else searcher_system_prompt_en
    if not model_format.lower().startswith('internlm'):
        interpreter_prompt += graph_fewshot_example_cn if lang == 'cn' else graph_fewshot_example_en
        plugin_prompt += fewshot_example_cn if lang == 'cn' else fewshot_example_en

    agent = MindSearchAgent(
        llm=llm,
        protocol=MindSearchProtocol(meta_prompt=datetime.now().strftime(
            'The current date is %Y-%m-%d.'),
                                    interpreter_prompt=interpreter_prompt,
                                    response_prompt=FINAL_RESPONSE_CN
                                    if lang == 'cn' else FINAL_RESPONSE_EN),
        searcher_cfg=dict(
            llm=llm,
            plugin_executor=ActionExecutor(
                BingBrowser(searcher_type='DuckDuckGoSearch',
                            topk=6,
                            api_key=os.environ.get('BING_API_KEY',
                                                   'YOUR BING API'))),
            protocol=MindSearchProtocol(
                meta_prompt=datetime.now().strftime(
                    'The current date is %Y-%m-%d.'),
                plugin_prompt=plugin_prompt,
            ),
            template=dict(input=searcher_input_template_cn
                          if lang == 'cn' else searcher_input_template_en,
                          context=searcher_context_template_cn
                          if lang == 'cn' else searcher_context_template_en)),
        max_turn=10)
    return agent


def main():
    st.title("MindSearch")
    lang = st.selectbox("言語", ["ja", "cn", "en"], index=0)
    model_format = st.selectbox("モデル", ["internlm_server"], index=0)
    question = st.text_input("質問を入力してください", "今日の東京の天気は？")
    if st.button("検索"):
        agent = init_agent(lang=lang, model_format=model_format)
        responses = []
        for agent_return in agent.stream_chat(question, as_dict=True):
            responses.append(agent_return)
            st.markdown(f"**状態**: {agent_return.state.name}")
            if agent_return.response:
                st.markdown(f"**回答**: {agent_return.response}")
            if agent_return.nodes:
                for node_name, node in agent_return.nodes.items():
                    st.markdown(f"**ノード**: {node_name}")
                    st.markdown(f"**内容**: {node['content']}")
                    st.markdown(f"**タイプ**: {node['type']}")
                    if 'response' in node:
                        st.markdown(f"**結果**: {node['response']}")
                    if 'detail' in node:
                        for action in node['detail']['actions']:
                            st.markdown(
                                f"**ツール**: {action['name']}，**パラメータ**: {action['parameters']}"
                            )
                            st.markdown(
                                f"**結果**: {action['result'][0]['content']}"
                            )
            if agent_return.adjacency_list:
                for node_name, neighbors in agent_return.adjacency_list.items():
                    st.markdown(f"**ノード**: {node_name}")
                    st.markdown(f"**隣接ノード**: {neighbors}")
        if responses:
            st.markdown(f"**最終状態**: {responses[-1].state.name}")
            if responses[-1].response:
                st.markdown(f"**最終回答**: {responses[-1].response}")


if __name__ == "__main__":
    main()