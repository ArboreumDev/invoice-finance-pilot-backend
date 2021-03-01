import {Stack, Button, Input, InputGroup, FormControl, FormLabel, Radio, RadioGroup} from "@chakra-ui/react"

import {axiosInstance, Invoice, FinanceStatus, ShipmentStatus} from "./Main"
import {useState} from "react";

interface Props {
  invoice: Invoice
}

const InvoiceStatusForm = ({ invoice }: Props) => {
    // const [date, setDate] = useState(invoice.startDate)
    const [status, setStatus] = useState(invoice.status)
    // const setComplete = () => {
    //     setStatus(LoanStatus.COMPLETED)
    // }
    // const setDefault = () => {
    //     setStatus(LoanStatus.DEFAULTED)
    // }
    const setFinanced = () => {
        setStatus(FinanceStatus.FINANCED)
    }
    // const updateDate = (e) => {
    //     setDate(e.target.value)
    // }
    const handleSubmit = (e) => {
        e.preventDefault()
        let {id, amount, destination, status:_, shippingStatus} = invoice
        // if (status == LoanStatus.LIVE) {
        //     startDate = date
        // }
        // else {
        //     endDate = date
        // }
        console.log('do something to invoice ', invoice)
        // axiosInstance.post("/loan", {id, amount, borrower, status, interest, startDate, endDate})
        //   .then((result)=>{
            //   console.log('new loan is ', result)
        //   })
    }

    // if (loan.status == LoanStatus.REQUESTED) {
    if (1) {
        return (
            <form onSubmit={handleSubmit}>
                <InputGroup size="sm">
                    <RadioGroup onChange={setStatus} value={status}>
                        <Stack direction="row">
                            <Radio value={FinanceStatus.FINANCED}>Financed</Radio>
                            <Radio value={FinanceStatus.REPAID}>Repaid</Radio>
                            <Radio value={FinanceStatus.REPAID}>Todo</Radio>
                        </Stack>
                    </RadioGroup>
                    <FormControl>
                        {/* <FormLabel>Start Date</FormLabel> */}
                        {/* <Input onChange={setFinanced} required placeholder="" width="170px" type="" name="date" /> */}
                        {/* <Input onChange={setFinanced} required placeholder="Start Date" width="170px" type="" name="date" /> */}
                    </FormControl>
                    <Button onClick={setFinanced} type="submit" m={2} size="sm">Update</Button>
                </InputGroup>
            </form>
        )
    }
    // else if (loan.status == LoanStatus.LIVE) {
    //     return (
    //         <form onSubmit={handleSubmit}>
    //             <InputGroup size="sm">
    //                 <FormControl>
    //                     <FormLabel>End Date</FormLabel>
    //                     <Input  onChange={updateDate} required width="170px" placeholder="End Date" type="date" />
    //                 </FormControl>
    //                 <Button onClick={setComplete} type="submit" m={2} size="sm" width="120px">Completed</Button>
    //                 <Button onClick={setDefault} type="submit" m={2} size="sm" width="120px">Defaulted</Button>
    //             </InputGroup>
    //         </form>
    //     )
    // }
}


export default InvoiceStatusForm