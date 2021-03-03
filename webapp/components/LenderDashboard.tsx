import {Box, Button, Grid, Heading, HStack, Text} from "@chakra-ui/react"
import {Line} from 'react-chartjs-2';
import useSWR from 'swr'
import AmountInput from "./AmountInput"
import {Invoice, fetcher, axiosInstance} from "./Main"
import { useRouter } from "next/router";
import React, { useEffect } from "react";

interface Props {
  invoices: Invoice[],
  isLoading: boolean,
  isError: Object
}

const LenderDashboard = ({invoices, isLoading, isError}: Props) => {
  const onInvest = () => {
    // invest in loan
    console.log("invested")
  }  

  // const { data: profits, error: profitError } = useSWR('/profit', fetcher, { refreshInterval: 1000 })
  // const r = axiosInstance.get("/v1/invoice", {}).then( (res) => {
    // console.log('res of get', res)
    // console.log('inv', invoices)
    // invoices = res.data
    // this.props.invoices = []
  // })


  if (isLoading) {
    return <Heading as="h2" size="lg" fontWeight="400" color="gray.500">
        Loading
      </Heading>
  }

  if (isError) {
    console.log(isError)
    return <Heading as="h2" size="lg" fontWeight="400" color="gray.500">
        There was an error
      </Heading>
  }

  const data = {
    // labels: profits ? Object.keys(profits):[],
    // datasets: [{
    //   label: 'Profit',
    //   data: profits ? Object.values(profits):[],
    //   borderWidth: 1,
    //   backgroundColor: "blue"
    // }],
  }

  const chart_options = {
    maintainAspectRatio: false
  }

  return (
    <>
      <Heading as="h2" size="lg" fontWeight="400" color="gray.500">
        Gurugrupa Dashboard
      </Heading>
      <Text mb={3} fontSize="xl">
        Finance your shipments
      </Text>
      <HStack>
        <Box w="lg">
          <Grid templateColumns={"repeat(" + 5 + ", 1fr)"} gap={3}>
            <Box width="100%" textAlign="center" bg="gray.100">
              Destination
            </Box>
            <Box width="100%" textAlign="center" bg="gray.100">
              Invoice Amount
            </Box>
            <Box width="100%" textAlign="center" bg="gray.100">
              Shipment Status
            </Box>
            <Box width="100%" textAlign="center" bg="gray.100">
              Status
            </Box>
            <Box width="100%" textAlign="center" bg="gray.100">
              Action
            </Box>
          </Grid>

          {invoices
            .filter((l) => l.status == "NONE")
            .map((l, idx) => (
              <>
                <Grid
                  p="10px"
                  h="90px"
                  templateColumns={"repeat(" + 5 + ", 1fr)"}
                  gap={3}
                  key={"loan_" + idx}
                >
                  <Box width="100%" textAlign="center">
                    {l.destination}
                  </Box>
                  <Box width="100%" textAlign="center">
                    {l.amount}
                  </Box>
                  <Box width="100%" textAlign="center">
                    {l.shippingStatus}
                  </Box>
                  <Box width="100%" textAlign="center">
                    {l.status}
                  </Box>
                  <Box width="100%" textAlign="center">
                    {/* <AmountInput value={100} /> */}
                    <Button size="sm">Finance</Button>
                  </Box>
                </Grid>
              </>
            ))}
        </Box>
        <Box p={3} w="md" h="400px" bg="teal.100" >
          <p>TODO: add data about Outstanding Debt here</p>
        </Box>
      </HStack>
    </>
  )
}

export default LenderDashboard
