import {Box, Heading, HStack, Text, Table,
  Thead,
  Tbody,
  Tfoot,
  Tr,
  Th,
  Td} from "@chakra-ui/react"
import {Invoice, FinanceStatus,ShipmentStatus} from "./Main"
import LoanStatusForm from "./InvoiceStatusForm";
import React from "react";
import InvoiceStatusForm from "./InvoiceStatusForm";

interface Props {
  invoices: Invoice[],
  isLoading: boolean,
  isError: Object
}

const AdminDashboard = ({invoices, isLoading, isError}: Props) => {

  const onFulfill = () => {
    // fulfill the loan
  }

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

  return (
    <Box>
      <Heading as="h2" size="lg" fontWeight="400" color="gray.500">
        Admin Dashboard
      </Heading>
      <HStack>
        <Box>
          <Table variant="simple">
            <Thead>
              <Tr>
                <Th>Destination</Th>
                <Th>Amount</Th>
                <Th>ShipmentStatus</Th>
                <Th>Status</Th>
                <Th>Update Status</Th>
              </Tr>
            </Thead>
            <Tbody>
              {invoices
                // .filter((l) => l.shipmentStatus == ShipmentStatus.AWAITING_SHIPMENT || l.shipmentStatus == ShipmentStatus.SHIPPING )
                .map((l, idx) => (
                  <>
                    <Tr>
                      <Td>{l.destination}</Td>
                      <Td>{l.amount}</Td>
                      <Td>{l.shippingStatus}</Td>
                      <Td>{l.status}</Td>
                      <Td><InvoiceStatusForm invoice={l} /></Td>
                    </Tr>
                  </>
                ))}
            </Tbody>
          </Table>
        </Box>
      </HStack>
    </Box>
  )
}

export default AdminDashboard
