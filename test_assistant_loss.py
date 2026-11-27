import copy,unittest
import torch
from transformers import Qwen3Config,Qwen3ForCausalLM
from train import assistant_loss

class AssistantLossTests(unittest.TestCase):
    def test_loss_and_gradients_match_full_masked_ce(self):
        torch.manual_seed(4);torch.set_num_threads(1)
        config=Qwen3Config(vocab_size=64,hidden_size=32,intermediate_size=64,num_hidden_layers=2,
                          num_attention_heads=4,num_key_value_heads=2,head_dim=8,max_position_embeddings=64,
                          attention_dropout=0.,use_cache=False)
        model=Qwen3ForCausalLM(config);other=copy.deepcopy(model)
        batch={'input_ids':torch.tensor([[2,3,4,5,6,7],[2,4,6,8,0,0]]),
               'attention_mask':torch.tensor([[1,1,1,1,1,1],[1,1,1,1,0,0]]),
               'labels':torch.tensor([[-100,-100,-100,5,6,7],[-100,-100,6,8,-100,-100]])}
        expected=model(**batch).loss;actual=assistant_loss(other,batch)
        torch.testing.assert_close(actual,expected,atol=1e-6,rtol=1e-6)
        expected.backward();actual.backward()
        for a,b in zip(model.parameters(),other.parameters()):
            if a.grad is not None:torch.testing.assert_close(a.grad,b.grad,atol=1e-6,rtol=1e-5)

if __name__=='__main__':unittest.main(verbosity=2)
