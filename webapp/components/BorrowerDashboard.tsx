import { Box, Heading, Text, Button, Input, InputGroup, HStack } from "@chakra-ui/react"
import {useState} from "react";
import {axiosInstance, FinanceStatus} from "./Main";



const BorrowerDashboard = () => {
  const [name, setName] = useState("")
  const [amount, setAmount] = useState(0)
  const [interest, setInterest] = useState(0.0)

  const updateName = (e) => {
    setName(e.target.value)
  }
  const updateAmount = (e) => {
    setAmount(e.target.value)
  }
  const updateInterest = (e) => {
    setInterest(e.target.value)
  }
  const handleSubmit = (e) => {
        e.preventDefault()
        axiosInstance.post("/create", {name, amount, interest})
          .then((result)=>{
          })
    }

  return (
    <Box>
      <Heading as="h2" size="lg" fontWeight="400" color="gray.500">
        Invoice Dashboard
      </Heading>
      <HStack>
        <Box p={3} w="md" h="400px">
          Add Invoice
          <form onSubmit={handleSubmit}>
            <InputGroup size="sm" m={2}>
              <Input  onChange={updateName} required width="300px" placeholder="Name" type="text" />
            </InputGroup>
            <InputGroup size="sm" m={2}>
              <Input  onChange={updateAmount} required width="300px" placeholder="Amount" type="number" />
            </InputGroup>
            <InputGroup size="sm" m={2}>
              <Input  onChange={updateInterest} required width="300px" placeholder="Interest Rate" type="text" />
            </InputGroup>
            <InputGroup size="sm" m={2}>
              <Button type="submit" m={2} size="sm" width="100px">Create</Button>
            </InputGroup>
        </form>
        </Box>
      </HStack>
    </Box>
  )
}

export default BorrowerDashboard
