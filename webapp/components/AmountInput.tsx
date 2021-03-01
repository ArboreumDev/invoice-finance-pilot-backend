import { Input, InputGroup, InputLeftAddon } from "@chakra-ui/react"

interface Props {
  value: number
}

const AmountInput = ({ value }: Props) => (
  <InputGroup size="sm">
    <InputLeftAddon background="white">₹</InputLeftAddon>
    <Input placeholder={"Amount"} value={value} />
  </InputGroup>
)
export default AmountInput
